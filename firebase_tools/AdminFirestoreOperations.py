from typing import TypeVar
from firebase_admin import firestore
from src.BaseClasses.FirestoreClient import AsyncPydanticFirestoreClient
from src._mappings import LEAGUE_MANAGER_ITEM_NAME_LIST, \
    ITEM_NAME_TO_PYDANTIC_MODEL_MAP, \
    ITEM_NAME_TO_COLLECTION_NAME_MAPPING
from src.logger import setup_logger

logger = setup_logger(__name__)

T = TypeVar('T')  # Generic type variable for your models


class AdminFirestoreClient:
    """Currently a Singleton class for AsyncPydanticFirestoreClient."""
    _instance = None

    def __new__(cls, db: firestore.client):
        # Singleton pattern ( dont forget that this accepts db as a parameter)
        if cls._instance is None:
            cls._instance = super(AdminFirestoreClient, cls).__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self, db: firestore.client):

        # Add all the clients for the different collections related to the League Manager
        for item_name in LEAGUE_MANAGER_ITEM_NAME_LIST:
            collection_name = ITEM_NAME_TO_COLLECTION_NAME_MAPPING[item_name]
            setattr(self, f'{collection_name}_client',
                    AsyncPydanticFirestoreClient(db=db, collection_name=collection_name,
                                                 model_cls=ITEM_NAME_TO_PYDANTIC_MODEL_MAP[item_name]))

    async def empty_all_collections(self):
        for collection_name in LEAGUE_MANAGER_ITEM_NAME_LIST:
            try:
                await getattr(self, f'{ITEM_NAME_TO_COLLECTION_NAME_MAPPING[collection_name]}_client').empty_collection()
            except Exception as e:
                logger.error(f'Error emptying collection {collection_name} with error {e}')


if __name__ == '__main__':
    exit('exiting because I have an exit() statement right under if __name__ == __main__')
    # >>> These are useful for manual admin changes/control
    #
    # > Create new sport, league, season

    # # > Test the Leagues Client
    # # Test adding the season to the league. Changes League[season_ids] and Season[league_id, status=active]
    # league_model = admin_firestore_client.leagues_client.add_season_to_league(league_id=league_model.id,
    #                                                                           season_id=season_model.id)
    # # Test removing the season from the league. Changes League[season_ids] and Season[league_id, status=inactive]
    # league_model = admin_firestore_client.leagues_client.remove_season_from_league(league_id=league_model.id,
    #                                                                                season_id=season_model.id)
    # # Test the delete league method. Changes Season[league_id, status=archived], first add a season to the league
    # league_model = admin_firestore_client.leagues_client.add_season_to_league(league_id=league_model.id,
    #                                                                           season_id=season_model.id)
    # admin_firestore_client.leagues_client.delete(league_id=league_model.id, hard_delete_children=False)
    #
    # # > Test the Seasons Client
    # Test adding a team to the season. Changes Season[team_ids]

    # Test User-Player-Club-Team-Season mechanics
    # - Register as Player and give extra permissions to create club
    #   - Create Player ( without payment information but with forms filled out)
    #   - Update Player (payment information is required before so permissions need to be updated)
    # - Player (or by admin) creates Club (with payment information) with Player as owner
    # - Create a Team with Club as captain
    # - Add Team to Season
    # - Add other players to Team (combined steps like Player to FreeAgent)
    # - Generate Games for Season
    # - Add Referee to Game

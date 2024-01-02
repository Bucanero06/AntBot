"""
* Required method set_id is called in the __init__ method to set the id of the lowest level class
* If attr is used in set_id required method, then the validator will be called before the id is set
    by using pre=True.
* For general validation although not required the standard has been use model_validator where white spaces are removed
    from string or List[string] as well as validation of the status and rules fields

"""
from typing import TypeVar, Union, Tuple, Optional, Type

from firebase_admin import firestore

T = TypeVar('T')  # Generic type variable for your models

from src.logger import setup_logger

logger = setup_logger(__name__)


class AsyncPydanticFirestoreClient:
    """
    Client for interacting with Firestore for general CRUD operations.

    Attributes
    ----------
    db : firestore.client
        Firestore client instance.
    collection : firestore.collection
        Reference to the Firestore collection.
    model_cls : Type[T]
        Reference to the specific model class (e.g., Team, Player).

    Methods
    -------
    create(item: T, return_just_id: bool = False) -> Union[str, Tuple[str, T]]:
        Create a new document in the Firestore collection.
    get(document_id: str) -> Optional[T]:
        Fetch a document from the Firestore collection.
    update(document_id: str, updated_data: dict) -> None:
        Update a specific document in the Firestore collection.
    get_all() -> list[T]:
        Fetch all documents from the Firestore collection.
    empty_collection() -> None:
        Deletes all documents from the Firestore collection.
    """

    def __init__(self, db: firestore.client, collection_name: str, model_cls: Type[T]):
        """
        Initialize the FirestoreClient.

        Parameters
        ----------
        db : firestore.client
            Firestore client instance.
        collection_name : str
            Name of the Firestore collection.
        model_cls : Type[T]
            Reference to the specific model class (e.g., Team, Player).
        """
        self.db = db

        self.collection = db.collection(collection_name)
        self.model_cls = model_cls  # This will store reference to the specific model class like Team, Player etc.

    async def create(self, item: T, return_just_id: bool = False) -> Union[str, Tuple[str, T]]:
        """
        Create a new document in the Firestore collection. If the provided item has a `set_id` method, that method's
        return value will be used as the document's ID in Firestore. Otherwise, Firestore generates a random ID.
        The created document's data is based on the provided item's data.

        Parameters
        ----------
        item : T
            Data to create the new document.
        return_just_id : bool, optional
            If set to True, only the ID of the created document will be returned. Default is False.

        Returns
        -------
        Union[str, Tuple[str, T]]
            If `return_just_id` is True, returns the ID of the created document. Otherwise, returns a tuple of the ID
            and the created document's data.

        Raises
        ------
        TypeError
            If the provided item is not an instance of `model_cls`.
        """
        # Check Type
        if not isinstance(item, self.model_cls):
            raise TypeError(f"Item is of type {type(item)} but should be {self.model_cls}")

        # Let Firestore generate ID if None is provided
        document_ref = self.collection.document(item.id.value)  # Fetch the document reference

        # Create the document in Firestore
        item_data = item.dict(exclude_unset=False)  # Get the data of the item as a dictionary
        item_data.pop("id", None)  # Exclude the object id from the data since it should the same as the document id
        document_ref.set(item_data)  # Create the document in Firestore

        # Reconstruct the item with the updated model data
        item = self.model_cls(**({'id': document_ref.id} | document_ref.get().to_dict()))  # Fetch the created document
        assert item.id
        return item if not return_just_id == True else item.id.value

    async def get(self, document_id: str) -> Optional[T]:
        """
        Fetch a document from the Firestore collection by its ID.

        Parameters
        ----------
        document_id : str
            ID of the document in the Firestore collection.

        Returns
        -------
        Optional[T]
            Data of the fetched document as an instance of `model_cls`, or None if no document is found.
        """
        document_ref = self.collection.document(document_id)
        if not document_ref.id:
            return None
        item_dict = document_ref.get().to_dict()
        if not item_dict:
            return None

        item = self.model_cls(**({'id': document_ref.id} | document_ref.get().to_dict()))
        return item

    async def update(self, document_id: str, updated_data: dict):
        """
        Update a specific document's data in the Firestore collection by its ID.

        Parameters
        ----------
        document_id : str
            ID of the document in the Firestore collection.
        updated_data : dict
            Dictionary containing the updated data.
        """
        document_ref = self.collection.document(document_id)  # Fixed this line
        document_ref.update(updated_data)
        item = self.model_cls(**({'id': document_ref.id} | document_ref.get().to_dict()))
        return item

    async def delete(self, document_id: str) -> dict:
        """
        Delete or archive a document in a collection.

        Note
        ----
        Deleting a document this way does not delete related objects like leagues, seasons, games, etc ...
            or their references. Instead use higher level methods or api to handle data in batches.
        Archiving is also recommended to keep references for future needs as well as a timer to delete archived
        """
        document_ref = self.collection.document(document_id)
        document_ref.delete()
        return {"status": "deleted", "id": document_id}

    async def get_all(self) -> list[T]:
        """
        Fetch all documents from the Firestore collection.

        Returns
        -------
        list[T]
            List of all documents' data as instances of `model_cls`.
        """
        docs = self.collection.stream()
        # return [self.model_cls(**doc.to_dict()) for doc in docs]

        items_list = []  # todo more efficient memory and speed and parallel
        for document_ref in docs:
            items_list.append(
                self.model_cls(
                    **{'id': document_ref.id, **document_ref.to_dict()}
                )
            )

        return items_list

    async def empty_collection(self):
        """
        Deletes all documents from the Firestore collection. This operation is irreversible.

        Warning
        -------
        Use this method with caution as it leads to the deletion of all documents from the Firestore collection.
        """
        batch = self.db.batch()
        docs = self.collection.stream()
        for doc in docs:
            batch.delete(doc.reference)
        batch.commit()

    # In the FirestoreClient class:

    async def add_to_batch(self, batch: firestore.WriteBatch, data: dict) -> firestore.WriteBatch:
        if not data:
            raise ValueError("Data is required for 'add' operation.")
        document_ref = self.collection.document()
        batch.set(document_ref, data)
        return batch

    async def update_to_batch(self, batch: firestore.WriteBatch, document_id: str, data: dict) -> firestore.WriteBatch:
        if not document_id or not data:
            raise ValueError("Document ID and data are required for 'update' operation.")
        document_ref = self.collection.document(document_id)
        batch.update(document_ref, data)
        return batch

    async def delete_from_batch(self, batch: firestore.WriteBatch, document_id: str) -> firestore.WriteBatch:
        if not document_id:
            raise ValueError("Document ID is required for 'delete' operation.")
        document_ref = self.collection.document(document_id)
        batch.delete(document_ref)
        return batch

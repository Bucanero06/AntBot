from h2o_wave import main, app, Q, ui


@app('/')
async def serve(q: Q):
    q.page['hello'] = ui.markdown_card(
        box='1 1 3 3',
        title='Hello',
        content='I should be running behind reverse proxy.'
    )
    await q.page.save()

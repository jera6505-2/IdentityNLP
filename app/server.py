from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import uvicorn, aiohttp, asyncio
from io import BytesIO
from hints import generatequote


from fastai import *
from fastai.vision import *

export_file_url = 'https://drive.google.com/uc?export=download&id=1gwn76dTvyyFueduCEhtGsnmFIuSSgFFn'
export_file_name = 'model_face.pkl'
classes = ['angelina_jolie', 'barack_obama', 'billie_eilish', 'chris_hemsworth', 'donald_trump', 'dwayne_johnson', 'gabrielle_union', 'jennifer_lawrence', 'jordan_michael', 'kawhi_leonard', 'keanu_reeves', 'keyli_jenner', 'lil_peep', 'naomi_scott', 'rafael_nadal', 'roger_federer', 'scarlett_johansson', 'selena_gomez', 'taylor_swift', 'Xi_Jinping']
path = Path(__file__).parent

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))


async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f:
                f.write(data)


async def setup_learner():
    await download_file(export_file_url, path / export_file_name)
    try:
        learn = load_learner(path, export_file_name)
        return learn
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise


loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()


@app.route('/')
async def homepage(request):
    html_file = path / 'view' / 'index.html'
    return HTMLResponse(html_file.open().read())


@app.route('/analyze', methods=['POST'])
async def analyze(request):
    img_data = await request.form()
    img_bytes = await (img_data['file'].read())
    img = open_image(BytesIO(img_bytes))
    prediction = learn.predict(img)[0]
    message = generatequote()
    print(message)
    return JSONResponse({'result': str(prediction) +'\n'+ str('Happy Birthday:') + str(message) })




if __name__ == '__main__':
    if 'serve' in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="info")

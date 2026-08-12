from fastapi import FastAPI, UploadFile

app = FastAPI(debug=True, title= 'Fast_Playground')

@app.post('/uploadfile')
async def handle_upload(file: UploadFile):
    return {'name':file.filename}
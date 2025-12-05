from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import aiofiles
from mcts.gqa import ImageQASystem
from config import Config
from pathlib import Path
import uuid

app = FastAPI(title="FTTracer Image QA API")

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(Config.OUTPUT_DIR)), name="static")


@app.post("/api/analyze")
async def analyze_image(image: UploadFile):
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

    # 生成唯一文件名
    file_ext = Path(image.filename).suffix
    temp_filename = f"{uuid.uuid4()}{file_ext}"
    temp_path = Config.OUTPUT_DIR / temp_filename

    try:
        # 保存临时文件
        async with aiofiles.open(temp_path, 'wb') as f:
            await f.write(await image.read())

        # 处理图像
        system = ImageQASystem()
        result = system.process(str(temp_path))

        # 返回结果
        return JSONResponse({
            "status": "success",
            "result": result.to_dict(),
            "visualization": f"/static/{result.visualization_path}"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 清理临时文件
        if temp_path.exists():
            temp_path.unlink()


def start_web_server(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)
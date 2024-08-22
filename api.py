from fastapi import FastAPI, File, UploadFile, Form
import os
from T1.read_data import read_data as read_data_t1
from T1.compare_data import compare_data as compare_data_t1
from T1.save_to_excel import save_to_excel as save_to_excel_t1
from T2.read_data import read_data as read_data_t2
from T2.compare_data import compare_data as compare_data_t2
from T2.save_to_excel import save_to_excel as save_to_excel_t2
from Tau.read_data import read_data as read_data_tau
from Tau.compare_data import compare_data as compare_data_tau
from Tau.save_to_excel import save_to_excel as save_to_excel_tau
from Amyloid.read_data import read_data as read_data_amyloid
from Amyloid.compare_data import compare_data as compare_data_amyloid
from Amyloid.save_to_excel import save_to_excel as save_to_excel_amyloid

app = FastAPI()

async def process_comparison(
    csv_file: UploadFile,
    excel_file: UploadFile,
    output_file: str,
    read_data,
    compare_data,
    save_to_excel
):
    try:
        # 업로드된 파일을 서버에 임시로 저장
        csv_path = f"temp_{csv_file.filename}"
        excel_path = f"temp_{excel_file.filename}"

        with open(csv_path, 'wb') as f:
            f.write(csv_file.file.read())

        with open(excel_path, 'wb') as f:
            f.write(excel_file.file.read())

        # 데이터 읽기 및 비교
        csv_df, excel_df_filtered = read_data(csv_path, excel_path)
        results_df, rois = compare_data(csv_df, excel_df_filtered)

        # 결과를 지정된 경로에 저장
        save_to_excel(results_df, output_file, rois)

        # 임시 파일 삭제
        os.remove(csv_path)
        os.remove(excel_path)

        return {"message": f"Comparison complete. Results saved to {output_file}"}

    except Exception as e:
        print(f"Error: {e}")
        return {"message": "Failed to compare files."}

@app.post("/T1/")
async def compare_files_t1(
    csv_file: UploadFile = File(...),
    excel_file: UploadFile = File(...),
    output_file: str = Form(...)
):
    return await process_comparison(csv_file, excel_file, output_file, read_data_t1, compare_data_t1, save_to_excel_t1)

@app.post("/T2/")
async def compare_files_t2(
    csv_file: UploadFile = File(...),
    excel_file: UploadFile = File(...),
    output_file: str = Form(...)
):
    return await process_comparison(csv_file, excel_file, output_file, read_data_t2, compare_data_t2, save_to_excel_t2)

@app.post("/Tau/")
async def compare_files_tau(
    csv_file: UploadFile = File(...),
    excel_file: UploadFile = File(...),
    output_file: str = Form(...)
):
    return await process_comparison(csv_file, excel_file, output_file, read_data_tau, compare_data_tau, save_to_excel_tau)

@app.post("/Amyloid/")
async def compare_files_amyloid(
    csv_file: UploadFile = File(...),
    excel_file: UploadFile = File(...),
    output_file: str = Form(...)
):
    return await process_comparison(csv_file, excel_file, output_file, read_data_amyloid, compare_data_amyloid, save_to_excel_amyloid)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, File, UploadFile, Form
import os
import requests
from fastapi.responses import FileResponse
from datetime import datetime

from AD.T1.read_data import read_data as read_data_t1
from AD.T1.compare_data import compare_data as compare_data_t1
from AD.T1.save_to_excel import save_to_excel as save_to_excel_t1
from AD.T2.read_data import read_data as read_data_t2
from AD.T2.compare_data import compare_data as compare_data_t2
from AD.T2.save_to_excel import save_to_excel as save_to_excel_t2
from AD.Tau.read_data import read_data as read_data_tau
from AD.Tau.compare_data import compare_data as compare_data_tau
from AD.Tau.save_to_excel import save_to_excel as save_to_excel_tau
from AD.Amyloid.read_data import read_data as read_data_amyloid
from AD.Amyloid.compare_data import compare_data as compare_data_amyloid
from AD.Amyloid.save_to_excel import save_to_excel as save_to_excel_amyloid
from PET.DAT.read_data import read_data as read_data_petDAT
from PET.DAT.compare_data import compare_data as compare_data_petDAT
from PET.DAT.save_to_excel import save_to_excel as save_to_excel_petDAT
from PET.General.read_data import read_data as read_data_petgeneral
from PET.General.compare_data import compare_data as compare_data_petgeneral
from PET.General.save_to_excel import save_to_excel as save_to_excel_petgeneral
from PET.Amyloid.read_data import read_data as read_data_petAmyloid
from PET.Amyloid.compare_data import compare_data as compare_data_petAmyloid
from PET.Amyloid.save_to_excel import save_to_excel as save_to_excel_petAmyloid
from PET.FDG.read_data import read_data as read_data_petFDG
from PET.FDG.compare_data import compare_data as compare_data_petFDG
from PET.FDG.save_to_excel import save_to_excel as save_to_excel_petFDG
from PET.Tau.read_data import read_data as read_data_petTau
from PET.Tau.compare_data import compare_data as compare_data_petTau
from PET.Tau.save_to_excel import save_to_excel as save_to_excel_petTau
from CTP.save_to_excel import save_to_excel as save_to_excel_ctp
from CTP.compare_data import compare_data as compare_data_ctp
from CTP.read_data import read_data as read_data_ctp
from AD.Normative.compare_data import compare_data as compare_data_normative
from AD.Normative.read_data import read_data as read_data_normative
from AD.Normative.save_to_excel import save_to_excel as save_to_excel_normative




app = FastAPI(title="데이터 비교 API", description="CSV 및 Excel 데이터를 비교하는 API", version="1.0.0")


TEAMS_WEBHOOK_URL = "https://neurophet2016.webhook.office.com/webhookb2/68c3850f-014d-4361-8035-655fe16f7aa8@0e0de970-ba32-48a4-a048-99d48e6eb282/IncomingWebhook/c3a5a9e99a41473a9f4d53d619aa0e87/a1b4164a-d122-4726-9b16-7896a06c2159/V2kLMW8k2Ybf2fyBleQleNixH_UVSyEaJqedNNaQiJtwc1"
SAVE_DIR = "./download"

def get_ngrok_url():
    try:
        # ngrok API에서 현재 터널 정보 가져오기
        response = requests.get("http://127.0.0.1:4040/api/tunnels")
        response.raise_for_status()
        tunnels = response.json().get("tunnels", [])
        for tunnel in tunnels:
            if tunnel.get("proto") == "https":
                return tunnel.get("public_url")
        raise Exception("HTTPS 터널을 찾을 수 없습니다.")
    except Exception as e:
        print(f"ngrok URL을 가져오는 중 오류 발생: {e}")
        return None


NGROK_URL = get_ngrok_url()
if NGROK_URL:
    print(f"ngrok URL: {NGROK_URL}")
else:
    print("ngrok URL을 가져오지 못했습니다.")


if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

async def process_comparison(
    csv_file: UploadFile,
    excel_file: UploadFile,
    endpoint: str,
    read_data,
    compare_data,
    save_to_excel
):
    """
    CSV 및 Excel 파일에서 데이터를 읽어와 비교한 후 결과를 Excel 파일로 저장합니다.
    """
    try:
        print("Reading files...")

        # 파일 저장 경로 설정
        csv_path = f"temp_{csv_file.filename}"
        excel_path = f"temp_{excel_file.filename}"

        # 파일 저장
        with open(csv_path, 'wb') as f:
            f.write(csv_file.file.read())
        with open(excel_path, 'wb') as f:
            f.write(excel_file.file.read())

        print("Files successfully saved.")

        # 결과 파일 기본 설정
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{endpoint}_{timestamp}.xlsx"
        file_path = os.path.join(SAVE_DIR, file_name)
        download_link = f"{NGROK_URL}/download/{file_name}"

        try:
            # 데이터 전처리 및 비교
            csv_df, excel_df_filtered = read_data(csv_path, excel_path)
            results_df, rois = compare_data(csv_df, excel_df_filtered)

            # 결과 파일 저장
            save_to_excel(results_df, file_path, rois)
            print(f"Results saved to: {file_path}")

            # Webhook 메시지 (정상 처리)
            message = {
                "text": (
                    f"{endpoint}데이터 비교가 완료되었습니다.\n"
                    f"**API Endpoint**: {endpoint}\n"
                    f"**결과 파일을 다운로드하려면 아래 링크를 클릭하세요.**\n"
                    f"[다운로드 링크]({download_link})"
                )
            }

        except Exception as e:
            print(f"Error during comparison: {e}")

            # Webhook 메시지 (에러 발생)
            message = {
                "text": (
                    f"{endpoint}데이터 비교 중 일부 오류가 발생했지만 결과 파일이 생성되었습니다.\n"
                    f"**API Endpoint**: {endpoint}\n"
                    f"**결과 파일을 다운로드하려면 아래 링크를 클릭하세요.**\n"
                    f"[다운로드 링크]({download_link})\n"
                    f"**에러 내용**: {str(e)}"
                )
            }

        # Teams Webhook 메시지 전송
        response = requests.post(TEAMS_WEBHOOK_URL, json=message)
        if response.status_code == 200:
            print("Teams Webhook 메시지 전송 성공!")
        else:
            print(f"Webhook 전송 실패: {response.status_code}, {response.text}")

        # 임시 파일 삭제
        os.remove(csv_path)
        os.remove(excel_path)

        return {
            "message": "비교 완료. 결과 파일이 생성되었으며 다운로드 링크가 Teams로 전송되었습니다.",
            "download_link": download_link,
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"message": f"파일 처리 중 치명적인 오류가 발생했습니다: {str(e)}"}


@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(SAVE_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"message": "파일을 찾을 수 없습니다."}


@app.get("/")
async def root():
    return {"message": "ngrok 테스트 서버 실행 중"}




@app.post("/AD/T1/")
async def compare_files_t1(
    csv_file: UploadFile = File(...),
    excel_file: UploadFile = File(...),
):
    return await process_comparison(csv_file, excel_file, "AD_T1", read_data_t1, compare_data_t1, save_to_excel_t1)

@app.post("/AD/T2/")
async def compare_files_t2(
    csv_file: UploadFile = File(...),
    excel_file: UploadFile = File(...),
):
    return await process_comparison(csv_file, excel_file, "AD_T2", read_data_t2, compare_data_t2, save_to_excel_t2)

@app.post("/AD/Tau/")
async def compare_files_tau(
    csv_file: UploadFile = File(...),
    excel_file: UploadFile = File(...),
):
    return await process_comparison(csv_file, excel_file, "AD_Tau", read_data_tau, compare_data_tau, save_to_excel_tau)

@app.post("/AD/Amyloid/")
async def compare_files_amyloid(
    csv_file: UploadFile = File(...),
    excel_file: UploadFile = File(...),
):
    return await process_comparison(csv_file, excel_file, "AD_Amyloid", read_data_amyloid, compare_data_amyloid, save_to_excel_amyloid)

@app.post("/AD/Normative/")
async def compare_files_normative(
    csv_file: UploadFile = File(...),
    excel_file: UploadFile = File(...),
):
    return await process_comparison(csv_file, excel_file, "AD_Normative", read_data_normative, compare_data_normative, save_to_excel_normative)

@app.post("/PET/DAT/")
async def compare_files_dat_suvr(
    csv_file: UploadFile = File(...),
    excel_file: UploadFile = File(...),
):
    return await process_comparison(csv_file, excel_file, "PET_DAT", read_data_petDAT, compare_data_petDAT, save_to_excel_petDAT)

@app.post("/PET/General/")
async def compare_files_general(
    csv_file: UploadFile = File(...),
    excel_file: UploadFile = File(...),
):
    return await process_comparison(csv_file, excel_file, "PET_General", read_data_petgeneral, compare_data_petgeneral, save_to_excel_petgeneral)

@app.post("/PET/Amyloid/")
async def compare_files_amyloid(
    csv_file: UploadFile = File(...),
    excel_file: UploadFile = File(...),
):
    return await process_comparison(csv_file, excel_file, "PET_Amyloid", read_data_petAmyloid, compare_data_petAmyloid, save_to_excel_petAmyloid)

@app.post("/PET/FDG/")
async def compare_files_fdg(
    csv_file: UploadFile = File(...),
    excel_file: UploadFile = File(...),
):
    return await process_comparison(csv_file, excel_file, "PET_FDG", read_data_petFDG, compare_data_petFDG, save_to_excel_petFDG)

@app.post("/PET/Tau/")
async def compare_files_tau(
    csv_file: UploadFile = File(...),
    excel_file: UploadFile = File(...),
):
    return await process_comparison(csv_file, excel_file, "PET_Tau", read_data_petTau, compare_data_petTau, save_to_excel_petTau)

@app.post("/CTP/CT/")
async def compare_files_ctp(
    csv_file: UploadFile = File(...),
    excel_file: UploadFile = File(...)
):
    return await process_comparison(csv_file, excel_file, "CTP_CT", read_data_ctp, compare_data_ctp, save_to_excel_ctp)

if __name__ == "__main__":
    import uvicorn
    ngrok_url = get_ngrok_url()
    if ngrok_url:
        print(f"ngrok URL: {ngrok_url}")  # ngrok URL을 로그에 출력
    else:
        print("ngrok URL을 가져올 수 없습니다. ngrok가 실행 중인지 확인하세요.")
    uvicorn.run(app, host="0.0.0.0", port=9000)


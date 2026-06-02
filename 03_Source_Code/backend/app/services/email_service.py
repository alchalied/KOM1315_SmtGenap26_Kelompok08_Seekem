import os
import httpx
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

load_dotenv()

# Setup Jinja2 Environment (mencari folder templates di dalam app/)
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(os.path.dirname(current_dir), "templates")
env = Environment(loader=FileSystemLoader(templates_dir))

class EmailService:
    @staticmethod
    async def send_contact_email(target_email: str, reporter_name: str, item_name: str, sender_name: str, sender_whatsapp: str, message: str, item_type: str = "hilang"):
        # Ambil URL GAS dari environment Railway
        gas_url = os.getenv("GAS_EMAIL_URL")
        
        if not gas_url:
            print("ERROR: GAS_EMAIL_URL tidak ditemukan di environment.")
            # Hanya print error, jangan di-raise agar ASGI server tidak crash
            return 
        
        # Konteks dinamis berdasarkan tipe laporan
        if item_type == "hilang":
            konteks = f"Seseorang mungkin telah menemukan barang Anda (<strong>{item_name}</strong>)."
        else:
            konteks = f"Seseorang mengklaim sebagai pemilik barang temuan Anda (<strong>{item_name}</strong>)."

        # HTML Sederhana dengan blockquote untuk pesan_koordinasi (message)
        pesan_html = f"<blockquote style='border-left: 4px solid #1a5632; padding-left: 15px; margin-left: 0; background: #f9f9f9; padding: 15px;'>{message}</blockquote>" if message else "<p><em>Tidak ada pesan khusus dari pengirim.</em></p>"

        try:
            # Render HTML menggunakan Jinja2
            template = env.get_template("email_template.html")
            html_content = template.render(
                reporter_name=reporter_name,
                konteks=konteks,
                sender_name=sender_name,
                pesan_html=pesan_html,
                sender_whatsapp=sender_whatsapp.replace('+', '')
            )
        except Exception as e:
            print(f"Jinja2 Render Error: {str(e)}")
            return

        # Sesuaikan struktur JSON dengan apa yang diminta oleh Google Apps Script
        payload = {
            "to": target_email,
            "subject": "Notifikasi Klaim Barang - SEEKEM IPB",
            "htmlBody": html_content
        }

        async with httpx.AsyncClient() as client:
            try:
                # follow_redirects=True sangat penting karena GAS selalu meredirect response
                response = await client.post(gas_url, json=payload, follow_redirects=True, timeout=15.0)
                
                if response.status_code != 200:
                    print(f"GAS HTTP ERROR [{response.status_code}]: {response.text}")
                    return
                
                response_data = response.json()
                if response_data.get("status") == "error":
                    print(f"GAS Internal Script Error: {response_data.get('message')}")
                    
            except httpx.RequestError as e:
                print(f"HTTPX NETWORK ERROR: {str(e)}")

    @staticmethod
    async def send_verification_email(target_email: str, user_name: str, verification_link: str):
        gas_url = os.getenv("GAS_EMAIL_URL")
        
        if not gas_url:
            print("ERROR: GAS_EMAIL_URL tidak ditemukan di environment.")
            return 
        
        try:
            template = env.get_template("verification_email_template.html")
            html_content = template.render(
                user_name=user_name,
                verification_link=verification_link
            )
        except Exception as e:
            print(f"Jinja2 Render Error (Verification): {str(e)}")
            return

        payload = {
            "to": target_email,
            "subject": "Verifikasi Email Pendaftaran - SEEKEM IPB",
            "htmlBody": html_content
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(gas_url, json=payload, follow_redirects=True, timeout=15.0)
                if response.status_code != 200:
                    print(f"GAS HTTP ERROR (Verification) [{response.status_code}]: {response.text}")
                    return
                
                response_data = response.json()
                if response_data.get("status") == "error":
                    print(f"GAS Internal Script Error (Verification): {response_data.get('message')}")
                    
            except httpx.RequestError as e:
                print(f"HTTPX NETWORK ERROR (Verification): {str(e)}")

    @staticmethod
    async def send_reset_password_email(target_email: str, user_name: str, reset_link: str):
        gas_url = os.getenv("GAS_EMAIL_URL")
        
        if not gas_url:
            print("ERROR: GAS_EMAIL_URL tidak ditemukan di environment.")
            return 
        
        try:
            template = env.get_template("reset_password_template.html")
            html_content = template.render(
                user_name=user_name,
                reset_link=reset_link
            )
        except Exception as e:
            print(f"Jinja2 Render Error (Reset Password): {str(e)}")
            return

        payload = {
            "to": target_email,
            "subject": "Reset Password - SEEKEM IPB",
            "htmlBody": html_content
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(gas_url, json=payload, follow_redirects=True, timeout=15.0)
                if response.status_code != 200:
                    print(f"GAS HTTP ERROR (Reset Password) [{response.status_code}]: {response.text}")
                    return
                
                response_data = response.json()
                if response_data.get("status") == "error":
                    print(f"GAS Internal Script Error (Reset Password): {response_data.get('message')}")
                    
            except httpx.RequestError as e:
                print(f"HTTPX NETWORK ERROR (Reset Password): {str(e)}")
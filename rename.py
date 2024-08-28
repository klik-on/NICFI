import json
import os
import subprocess
import re
import time
import requests

# Meminta input dari pengguna untuk nilai mosaic_name baru
new_mosaic_name = input("Enter new mosaic_name:")

# Path ke direktori yang berisi file JSON
directory = r'../FGHI'

# Daftar file yang telah diperbarui dan ID order
updated_files = []
order_ids = []

# Langkah 1: Mengganti mosaic_name di semua file JSON
for filename in os.listdir(directory):
    if filename.endswith("-basemap-order.json"):  # Memfilter file yang sesuai dengan pola nama
        file_path = os.path.join(directory, filename)
        
        # Membaca dan memodifikasi file JSON
        with open(file_path, 'r') as file:
            data = json.load(file)

        modified = False
        for product in data.get("products", []):
            if "mosaic_name" in product:
                product["mosaic_name"] = new_mosaic_name
                modified = True

        if modified:
            # Menyimpan perubahan kembali ke file
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)
            updated_files.append(file_path)
            print(f"Updated {filename}")
            
            # Membangun dan menjalankan perintah planet orders create
            command = f"planet orders create {file_path}"
            
            try:
                result = subprocess.run(command, check=True, shell=True, text=True, capture_output=True)
                output = result.stdout
                print(f"Successfully ran command for {filename}")
                
                # Menyimpan ID dari output
                match = re.search(r'"id": "([a-f0-9\-]+)"', output)
                if match:
                    order_ids.append(match.group(1))
                else:
                    print(f"ID not found in output for {filename}")

            except subprocess.CalledProcessError as e:
                print(f"Failed to run command for {filename}: {e}")

# Fungsi untuk memeriksa status order
def check_order_status(order_id):
    url = f"https://api.planet.com/compute/ops/orders/v2/{order_id}"
    response = requests.get(url, auth=('PLAKa6eb33a6a23448af90538749347e73a0', ''))
    if response.status_code == 200:
        data = response.json()
        status = data.get("last_message", "")
        if status == "Manifest delivery completed":
            return True
        else:
            print(f"Order {order_id} status: {status}")
            return False
    else:
        print(f"Failed to check status for {order_id}: {response.status_code}")
        return False

# Langkah 2: Membuat file Python untuk perintah planet orders download
with open('generate_download_commands.py', 'w') as file:
    file.write('import subprocess\n\n')
    for order_id in order_ids:
        # Periksa status order sebelum menambahkan perintah download
        while not check_order_status(order_id):
            print(f"Order {order_id} is not ready yet. Checking again in 30 seconds...")
            time.sleep(30)
        file.write(f'subprocess.run("planet orders download {order_id}", check=True, shell=True)\n')

print("All files updated, commands executed, and download commands generated.")

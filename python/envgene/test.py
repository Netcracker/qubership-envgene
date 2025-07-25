
import time
from envgenehelper import  crypt

start = time.perf_counter()
# crypt.encrypt_all_cred_files_for_env()
crypt.decrypt_all_cred_files_for_env()
end = time.perf_counter()
print(f"Время выполнения A: {end - start:.6f} секунд")

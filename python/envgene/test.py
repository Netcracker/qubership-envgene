
from envgenehelper import crypt
from time import perf_counter

# Start the stopwatch / counter
t1_start = perf_counter()

print(crypt.decrypt_file(
    '/workspace/instance-project/environments/REDACTED-ocp-01/credentials/cluster-creds.yml', in_place=True))
# crypt.decrypt_all_cred_files_for_env()
# Stop the stopwatch / counter
t1_stop = perf_counter()

print("Elapsed time:", t1_stop - t1_start)


# print(len(crypt.get_all_necessary_cred_files()))

# crypt.encrypt_file('/workspace/instance-project/environments/REDACTED-ocp-mdc5-08c/env-1/Credentials/credentials.yml')

import requests
from pathlib import Path

from envgenehelper.errors import IntegrationError


class ApiClient:

    def __init__(self, verify_ssl=False):
        self.verify_ssl = verify_ssl

    def get_json(self, url, headers=None, timeout=30):
        try:
            response = requests.get(
                url,
                headers=headers or {},
                verify=self.verify_ssl,
                timeout=timeout,
            )
            if response.status_code == 404:
                return {}
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            raise IntegrationError(f"GET request failed for URL: {url}. Error: {e}")

    def download_file(self, url: str, dest: str, headers: dict = None,
                      chunk_size: int = 8192, timeout: int = 60):
        try:
            headers = headers or {}
            Path(dest).parent.mkdir(parents=True, exist_ok=True)

            with requests.get(
                    url,
                    headers=headers,
                    stream=True,
                    verify=self.verify_ssl,
                    timeout=timeout,
            ) as r:
                r.raise_for_status()

                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)

            return dest

        except requests.RequestException as e:
            raise IntegrationError(f"File download failed for URL: {url}. Error: {e}")

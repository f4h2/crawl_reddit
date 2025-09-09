from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import Config


class MongoDBConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBConnection, cls).__new__(cls)
            cls._instance._client = None
        return cls._instance

    def connect(self):
        if self._client is None:
            try:
                self._client = MongoClient(Config.MONGO_DB_HOST)
                self._client.server_info()  # Kiểm tra kết nối
                print("Kết nối MongoDB thành công")
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                print(f"Lỗi khi kết nối MongoDB: {e}")
                raise
        return self._client

    def get_client(self):
        if self._client is None:
            self.connect()
        return self._client

    def close(self):
        if self._client:
            self._client.close()
            self._client = None
            print("Đã đóng kết nối MongoDB")
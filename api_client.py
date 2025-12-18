# api_client.py
import requests
import os

class APIClient:
    def __init__(self, base_url=None, token=None):
        self.base_url = base_url or os.getenv("API_URL", "https://election-are-near-backend.onrender.com")
        self.token = token

    # ==================== NEW: Generic GET/POST ====================
    def get(self, endpoint, params=None, method="GET"):
        """Generic API request"""
        url = f"{self.base_url}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, params=params, headers=self.headers())
        elif method == "POST":
            response = requests.post(url, json=params, headers=self.headers())
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    # ==================== NEW: Session Status Check ====================
    def check_session_status(self):
        """Check if current session is valid"""
        url = f"{self.base_url}/session/status"
        response = requests.get(url, headers=self.headers())
        response.raise_for_status()
        return response.json()
    
    # ==================== NEW: Refresh Session ====================
    def refresh_session(self):
        """Refresh session expiry"""
        url = f"{self.base_url}/refresh-session"
        response = requests.post(url, headers=self.headers())
        response.raise_for_status()
        return response.json()
    
    
    # ---------- LOGIN ----------
    def login(self, username, password):
        url = f"{self.base_url}/login"
        data = {"username": username, "password": password}
        response = requests.post(url, data=data)
        response.raise_for_status()
        res = response.json()
        self.token = res["access_token"]
        return res

    # ---------- TOKEN HEADER ----------
    def headers(self):
        if not self.token:
            return {}  # Allow unauthenticated requests (fallback)
        return {"Authorization": f"Bearer {self.token}"}

    # ---------- FETCH VOTERS (PAGINATED) ----------
    def get_voters(self, limit=5000, offset=0, search=None):
        params = {"limit": limit, "offset": offset}
        if search:
            params["search"] = search
        
        url = f"{self.base_url}/voters"
        response = requests.get(url, params=params, headers=self.headers())
        response.raise_for_status()
        return response.json()

    # ---------- FETCH SURVEYS ----------
    def get_surveys(self, limit=300, offset=0):
        url = f"{self.base_url}/surveys"
        response = requests.get(url, params={"limit": limit, "offset": offset}, headers=self.headers())
        response.raise_for_status()
        return response.json()

    # ---------- VOTER FILTERS ----------
    def get_voter_filters(self):
        url = f"{self.base_url}/voters/filters"
        response = requests.get(url, headers=self.headers())
        response.raise_for_status()
        return response.json()

    # ---------- SUMMARY ----------
    def get_voter_summary(self):
        url = f"{self.base_url}/voters/summary"
        response = requests.get(url, headers=self.headers())
        response.raise_for_status()
        return response.json()

    # ---------- FILTERED LIST ----------
    def get_voter_list(self, **params):
        url = f"{self.base_url}/voters/list"
        response = requests.get(url, params=params, headers=self.headers())
        response.raise_for_status()
        return response.json()

    # ---------- SUBMIT SURVEY ----------
    def submit_survey(self, data):
        url = f"{self.base_url}/submit-survey"
        response = requests.post(url, json=data, headers=self.headers())
        response.raise_for_status()
        return response.json()

    # # ---------- LOGOUT ----------
    # def logout(self):
    #     if self.token:
    #         url = f"{self.base_url}/logout"
    #         try:
    #             headers = {"Authorization": f"Bearer {self.token}"}
    #             requests.post(url, headers=headers)
    #         except Exception:
    #             pass
    #     self.token = None
    
    # ==================== UPDATED: Logout ====================
    def logout(self):
        """Logout and clear session"""
        if self.token:
            url = f"{self.base_url}/logout"
            try:
                response = requests.post(url, headers=self.headers())
                response.raise_for_status()
            except Exception as e:
                print(f"Logout error: {e}")
        
        self.token = None


    # ---------- CHECK USER STATUS ----------
    def get_user_status(self):
        """Get current user status (active, allocation info)"""
        url = f"{self.base_url}/user/status"
        response = requests.get(url, headers=self.headers())
        response.raise_for_status()
        return response.json()
    
    # ---------- CREATE USER ----------
    def create_user(self, username, password):
        url = f"{self.base_url}/add-subuser"
        data = {
            "username": username,
            "password": password
        }
        response = requests.post(url, json=data, headers=self.headers())
        response.raise_for_status()
        return response.json()

    # ---------- GET USERS (by parent_id) ----------
    def get_users(self, parent_id=None):
        url = f"{self.base_url}/users"
        params = {}
        if parent_id:
            params["parent_id"] = parent_id
        response = requests.get(url, params=params, headers=self.headers())
        response.raise_for_status()
        return response.json()


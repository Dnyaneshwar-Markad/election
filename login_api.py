
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import jwt, JWTError
from datetime import datetime, timedelta, date
import psycopg
from typing import Optional, List, Any, Dict, Tuple
import uuid

token_blacklist = set()

# ==================== CONFIG ====================
SECRET_KEY = "your-secret-key-change-this-12345"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 7 days
SESSION_TIMEOUT_HOURS = 48
INACTIVITY_TIMEOUT_MINUTES = 400

# Database connection string (your NeonDB)
DATABASE_URL = "postgresql://neondb_owner:npg_rs1bVogh7EtU@ep-weathered-math-a1pj9ocn-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

app = FastAPI(title="Login API")

# CORS - Allow all origins (change in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# ==================== MODELS ====================
class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str
    main_admin_id: int
    section_no: Optional[int] = None
    allocated: Optional[int] = None  # Added
    users: Optional[int] = None       # Added
    inactivity_timeout: int = INACTIVITY_TIMEOUT_MINUTES
    profile: Optional[Dict[str, Any]]

class ActivityUpdateRequest(BaseModel):
    """Request to update last activity timestamp"""
    pass

class UserResponse(BaseModel):
    user_id: int
    username: str
    role: str
    main_admin_id: int
    section_no: Optional[int] = None
    allocated: Optional[int] = None  # Added
    users: Optional[int] = None       # Added

class SurveyInput(BaseModel):
    VoterID: Optional[int]
    VEName: Optional[str]
    Sex: Optional[str]
    HouseNo: Optional[str]
    Landmark: Optional[str]
    VAddress: Optional[str]
    Mobile: Optional[str]
    PartNo: Optional[int]
    SectionNo: Optional[int]
    VotersCount: Optional[int]
    Male: Optional[int]
    Female: Optional[int]
    Caste: Optional[str]
    Age: Optional[int]


class SurveySubmissionRequest(BaseModel):
    """Request body for submitting survey and marking voters as visited."""
    family_head_id: int
    selected_family_ids: list[int] = []
    house_number: Optional[str] = None
    landmark: Optional[str] = None
    mobile: Optional[str] = None
    caste: Optional[str] = None
    visited: int = 1
    main_admin_id: Optional[int] = None

class CreateSubUserRequest(BaseModel):
    username: str
    password: str

class CreateSubUserResponse(BaseModel):
    success: bool
    subuser_id: int
    parent_id: int
class SurveySubmissionResponse(BaseModel):
    """Response after survey submission."""
    success: bool
    message: str
    survey_id: Optional[int] = None

# ==================== DATABASE ====================
def get_connection():
    return psycopg.connect(DATABASE_URL)

# ==================== HELPER: Generate Session ID ====================
def generate_session_id():
    """Generate unique session ID"""
    return str(uuid.uuid4())

# ==================== HELPER: Cleanup Expired Sessions ====================
def cleanup_expired_sessions():
    """Remove expired sessions (including inactivity timeout)"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # ✅ CLEANUP BASED ON SESSION EXPIRY OR INACTIVITY
                cur.execute("""
                    UPDATE "User"
                    SET "Active" = FALSE,
                        "SessionID" = NULL,
                        "SessionExpiry" = NULL,
                        "LastActivity" = NULL
                    WHERE (
                        "SessionExpiry" < NOW() 
                        OR "LastActivity" < NOW() - INTERVAL '%s minutes'
                    )
                    AND "Active" = TRUE
                """, (INACTIVITY_TIMEOUT_MINUTES,))
                conn.commit()
                
                expired_count = cur.rowcount
                if expired_count > 0:
                    print(f"🧹 Cleaned up {expired_count} expired/inactive sessions")
                    
    except Exception as e:
        print(f"❌ Error cleaning up sessions: {e}")

# ==================== UPDATED: Validate User ====================
def validate_user(username: str, password: str):
    """Check username and password"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:  
                cur.execute("""
                    SELECT "UserID", "Username", "Role", "ParentID", "SectionNo",
                           "Active", "Allocated", "Users", "SessionID", "SessionExpiry",
                           "LastActivity"
                    FROM "User"
                    WHERE "Username" = %s AND "Password" = %s
                """, (username, password))
                
                row = cur.fetchone()
                if not row:
                    return None
                
                (user_id, username, role, parent_id, section_no, 
                 active, allocated, users, session_id, session_expiry,
                 last_activity) = row
                
                # ✅ CHECK IF ALREADY LOGGED IN (and not inactive)
                if active and session_id:
                    # Check session expiry
                    if session_expiry and session_expiry > datetime.utcnow():
                        # Check inactivity
                        if last_activity:
                            inactive_duration = datetime.utcnow() - last_activity
                            if inactive_duration.total_seconds() < (INACTIVITY_TIMEOUT_MINUTES * 60):
                                return {
                                    "error": "already_logged_in",
                                    "message": "This account is already logged in from another device"
                                }
                
                main_admin_id = user_id if parent_id in (None, 0) else parent_id
                
                return {
                    "user_id": user_id,
                    "username": username,
                    "role": role,
                    "main_admin_id": main_admin_id,
                    "section_no": section_no,
                    "allocated": allocated or 0,
                    "users": users or 0
                }
                
    except Exception as e:
        print(f"Database error: {e}")
        return None
    
# ==================== JWT FUNCTIONS ====================
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ==================== FIXED: Get Current User ====================
def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validate JWT token and session (with inactivity check)"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        session_id = payload.get("session_id")
        
        if not user_id or not session_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT "Active", "SessionID", "SessionExpiry", "LastActivity"
                    FROM "User"
                    WHERE "UserID" = %s
                """, (user_id,))
                
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=401, detail="User not found")
                
                active, db_session_id, session_expiry, last_activity = row
                
                # Check session match
                if db_session_id != session_id:
                    raise HTTPException(
                        status_code=401, 
                        detail="Session invalid - logged in from another device"
                    )
                
                # Check session expiry
                if session_expiry and session_expiry < datetime.utcnow():
                    raise HTTPException(
                        status_code=401, 
                        detail="Session expired - please login again"
                    )
                
                # ✅ CHECK INACTIVITY TIMEOUT
                if last_activity:
                    inactive_duration = datetime.utcnow() - last_activity
                    inactive_seconds = inactive_duration.total_seconds()
                    # ✅ DEBUG: Log inactivity duration
                    print(f"🕐 User {user_id}: Inactive for {int(inactive_seconds/60)} minutes")
                    
                    if inactive_seconds > (INACTIVITY_TIMEOUT_MINUTES * 60):
                        # Auto-logout due to inactivity
                        cur.execute("""
                            UPDATE "User"
                            SET "Active" = FALSE,
                                "SessionID" = NULL,
                                "SessionExpiry" = NULL,
                                "LastActivity" = NULL
                            WHERE "UserID" = %s
                        """, (user_id,))
                        conn.commit()
                        
                        raise HTTPException(
                            status_code=401, 
                            detail=f"Session expired due to {INACTIVITY_TIMEOUT_MINUTES} minutes of inactivity"
                        )
                
                # Check active status
                if not active:
                    raise HTTPException(
                        status_code=401, 
                        detail="Session terminated"
                    )
        
        return {
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
            "role": payload.get("role"),
            "main_admin_id": payload.get("main_admin_id"),
            "section_no": payload.get("section_no"),
            "session_id": session_id
        }
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_user_profile_data(main_admin_id: int):
    """
    Fetch FullName, Symbol, SerialNo for main admin
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "UserID", "FullName", "Symbol", "SerialNo"
                FROM "User"
                WHERE "UserID" = %s
                """,
                (main_admin_id,)
            )
            row = cur.fetchone()
            if not row:
                return None

            columns = [desc[0] for desc in cur.description]
            return dict(zip(columns, row))


# ==================== ENDPOINTS ====================
@app.get("/")
def root():
    return {"message": "Login API is running", "docs": "/docs"}

@app.get("/health")
def health_check():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        
        return {
            "status": "UP",
            "database": "CONNECTED",
            "inactivity_timeout_minutes": INACTIVITY_TIMEOUT_MINUTES,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        return {
            "status": "DOWN",
            "database": "DISCONNECTED",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/login", response_model=LoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    cleanup_expired_sessions()

    user = validate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.get("error"):
        raise HTTPException(status_code=403, detail=user["message"])

    session_id = generate_session_id()
    expiry = datetime.utcnow() + timedelta(hours=SESSION_TIMEOUT_HOURS)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE "User"
                SET "Active"=TRUE,
                    "LastLogin"=NOW(),
                    "SessionID"=%s,
                    "SessionExpiry"=%s,
                    "LastActivity"=NOW()
                WHERE "UserID"=%s
            """, (session_id, expiry, user["user_id"]))
            conn.commit()

    token = create_access_token({
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"],
        "main_admin_id": user["main_admin_id"],
        "section_no": user["section_no"],
        "session_id": session_id
    })

    profile_data = get_user_profile_data(user["main_admin_id"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"],
        "main_admin_id": user["main_admin_id"],
        "section_no": user["section_no"],
        "allocated": user["allocated"],
        "users": user["users"],
        "inactivity_timeout": INACTIVITY_TIMEOUT_MINUTES,
        "profile": {
            "status": True,
            "data": profile_data
        }
    }



# ==================== UPDATE ACTIVITY ENDPOINT ====================
@app.post("/activity/update")
def update_activity(current_user = Depends(get_current_user)):
    """
    ✅ NEW ENDPOINT: Update last activity timestamp
    Call this from frontend on user interactions
    """
    try:
        user_id = current_user.get("user_id")
        session_id = current_user.get("session_id")
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE "User"
                    SET "LastActivity" = NOW()
                    WHERE "UserID" = %s AND "SessionID" = %s
                """, (user_id, session_id))
                conn.commit()
        
        return {
            "status": "success",
            "message": "Activity updated",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
# ==================== ENHANCED LOGOUT ENDPOINT ====================
@app.post("/logout")
def logout(current_user = Depends(get_current_user)):
    """Logout endpoint"""
    try:
        user_id = current_user.get("user_id")
        session_id = current_user.get("session_id")
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE "User"
                    SET "Active" = FALSE,
                        "SessionID" = NULL,
                        "SessionExpiry" = NULL,
                        "LastActivity" = NULL
                    WHERE "UserID" = %s AND "SessionID" = %s
                """, (user_id, session_id))
                conn.commit()
        
        print(f"✅ Logout - UserID: {user_id}")
        
        return {"status": "success", "message": "Logged out successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== NEW: Refresh Session Endpoint ====================
@app.post("/refresh-session")
def refresh_session(current_user = Depends(get_current_user)):
    """
    Refresh session expiry time (call this periodically from frontend)
    """
    try:
        user_id = current_user.get("user_id")
        session_id = current_user.get("session_id")
        
        # Extend session expiry
        new_expiry = datetime.utcnow() + timedelta(hours=SESSION_TIMEOUT_HOURS)
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE "User"
                    SET "SessionExpiry" = %s
                    WHERE "UserID" = %s AND "SessionID" = %s
                """, (new_expiry, user_id, session_id))
                conn.commit()
        
        return {
            "status": "success",
            "message": "Session refreshed",
            "expires_at": new_expiry.isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error refreshing session: {str(e)}"
        )

# ==================== NEW: Check Session Status ====================
@app.get("/session/status")
def check_session_status(current_user = Depends(get_current_user)):
    """Check session status (includes inactivity check)"""
    try:
        user_id = current_user.get("user_id")
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT "Active", "SessionExpiry", "LastActivity"
                    FROM "User"
                    WHERE "UserID" = %s
                """, (user_id,))
                
                row = cur.fetchone()
                if not row:
                    return {"valid": False, "reason": "User not found"}
                
                active, session_expiry, last_activity = row
                
                if not active:
                    return {"valid": False, "reason": "Session inactive"}
                
                if session_expiry and session_expiry < datetime.utcnow():
                    return {"valid": False, "reason": "Session expired"}
                
                # ✅ CHECK INACTIVITY
                if last_activity:
                    inactive_duration = datetime.utcnow() - last_activity
                    inactive_minutes = int(inactive_duration.total_seconds() / 60)
                    
                    if inactive_minutes >= INACTIVITY_TIMEOUT_MINUTES:
                        return {
                            "valid": False, 
                            "reason": f"Inactive for {inactive_minutes} minutes"
                        }
                    
                    return {
                        "valid": True,
                        "expires_at": session_expiry.isoformat() if session_expiry else None,
                        "last_activity": last_activity.isoformat(),
                        "inactive_minutes": inactive_minutes,
                        "timeout_minutes": INACTIVITY_TIMEOUT_MINUTES
                    }
                
                return {
                    "valid": True,
                    "expires_at": session_expiry.isoformat() if session_expiry else None
                }
    
    except Exception as e:
        return {"valid": False, "reason": str(e)}

@app.get("/me", response_model=UserResponse)
def get_me(current_user = Depends(get_current_user)):
    """Get current logged-in user info"""
    return current_user

@app.get("/protected")
def protected_route(current_user = Depends(get_current_user)):
    """Example protected route - requires valid JWT token"""
    return {
        "message": f"Hello {current_user['username']}!",
        "user": current_user
    }


@app.get("/user/profile")
def get_user_profile(current_user=Depends(get_current_user)):
    """
    Returns:
    - Admin user -> own FullName, Symbol, SerialNo
    - Sub user  -> parent admin's FullName, Symbol, SerialNo
    """

    try:
        user_id = current_user.get("user_id")
        parent_id = current_user.get("parent_id")
        main_admin_id = current_user.get("main_admin_id") or current_user.get("user_id")

        if not user_id:
            raise HTTPException(status_code=403, detail="Invalid user session")

        # Decide whose data to fetch
        # target_user_id = parent_id if parent_id not in (None, 0) else user_id

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT "UserID", "FullName", "Symbol", "SerialNo"
                    FROM "User"
                    WHERE "UserID" = %s
                    """,
                    (main_admin_id,)
                )

                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="User not found")

                columns = [desc[0] for desc in cur.description]
                result = dict(zip(columns, row))

        return {
            "status": True,
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching user profile: {str(e)}"
        )


@app.get("/users")
def list_users(parent_id: Optional[int] = None, current_user = Depends(get_current_user)):
    """List users created under a parent admin (for settings page)."""
    try:
        admin_id = parent_id or current_user.get("user_id")
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT "UserID", "Username", "Role", "CreatedAt"
                    FROM "User"
                    WHERE "ParentID" = %s
                    ORDER BY "CreatedAt" DESC
                """, (admin_id,))
                
                rows = cur.fetchall()
                columns = [d[0] for d in cur.description]
                users = [dict(zip(columns, row)) for row in rows]
        
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")
from datetime import datetime

@app.post("/add-subuser", response_model=CreateSubUserResponse)
def add_subuser(
    request: CreateSubUserRequest,
    current_user=Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create subusers")

    parent_id = current_user["user_id"]
    section_no = current_user["section_no"]
    if section_no is None:
        raise HTTPException(
            status_code=400,
            detail="Admin has no section assigned"
        )

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                # ✅ CHECK ALLOCATION LIMIT
                cur.execute("""
                    SELECT "Allocated", "Users"
                    FROM "User"
                    WHERE "UserID" = %s
                """, (parent_id,))
                
                admin_data = cur.fetchone()
                if not admin_data:
                    raise HTTPException(status_code=404, detail="Admin not found")
                
                allocated, current_users = admin_data
                allocated = allocated or 0
                current_users = current_users or 0
                # ✅ CHECK IF LIMIT EXCEEDED
                if current_users >= allocated:
                    raise HTTPException(
                        status_code=403,
                        detail=f"❌ Allocation limit exceeded! You can only create {allocated} subusers. Current: {current_users}"
                    )

                cur.execute(
                    'SELECT 1 FROM "User" WHERE "Username"=%s',
                    (request.username,)
                )
                if cur.fetchone():
                    raise HTTPException(status_code=400, detail="Username already exists")

                cur.execute("""
                    INSERT INTO "User"
                    ("Username","Password","Role","ParentID","CreatedAt","SectionNo","Active")
                    VALUES (%s,%s,'subuser',%s,%s,%s,FALSE)
                    RETURNING "UserID"
                """, (
                    request.username,
                    request.password,
                    parent_id,
                    date.today(),
                    section_no
                ))

                user_id = cur.fetchone()[0]
                # ✅ INCREMENT USERS COUNT FOR ADMIN
                cur.execute("""
                    UPDATE "User"
                    SET "Users" = "Users" + 1
                    WHERE "UserID" = %s
                """, (parent_id,))

                conn.commit()
                print(f"✅ Subuser created: {request.username} (Parent: {parent_id}, Users: {current_users + 1}/{allocated})")
                
        return {
            "success": True,
            "subuser_id": user_id,
            "parent_id": parent_id
        }

    except HTTPException:
        raise
    except Exception as e:
        print("ADD SUBUSER ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/set-allocation")
def set_user_allocation(
    user_id: int,
    allocated: int,
    current_user = Depends(get_current_user)
):
    """
    Set allocation limit for an admin user
    (Only super admin can do this - you can add role check)
    """
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE "User"
                    SET "Allocated" = %s
                    WHERE "UserID" = %s AND "Role" = 'admin'
                """, (allocated, user_id))
                
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Admin user not found")
                
                conn.commit()
        
        return {
            "success": True,
            "message": f"Allocation set to {allocated} for user {user_id}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== NEW: CHECK USER STATUS ====================
@app.get("/user/status")
def get_user_status(current_user = Depends(get_current_user)):
    """
    Get current user's status
    - Active status
    - Allocation info (for admins)
    """
    try:
        user_id = current_user.get("user_id")
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT "Active", "Allocated", "Users", "Role"
                    FROM "User"
                    WHERE "UserID" = %s
                """, (user_id,))
                
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="User not found")
                
                active, allocated, users, role = row
                
                return {
                    "user_id": user_id,
                    "active": active,
                    "allocated": allocated or 0,
                    "users": users or 0,
                    "role": role,
                    "remaining": max(0, (allocated or 0) - (users or 0))
                }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voters")
def get_voters(search: Optional[str] = None, limit: int = 1000, offset: int = 0, current_user = Depends(get_current_user)):
    """
    Return voter list with Mobile number from SurveyData.
    Mobile is fetched via LEFT JOIN on VoterID.
    """
    try:
        main_admin_id = current_user.get("main_admin_id") or current_user.get("user_id")
        visited_col = f"Visited_{main_admin_id}"
        section_no = current_user.get("section_no")

        with get_connection() as conn:


            visited_expr = f'"{visited_col}"' if col_exists else '"Visited"'

            # Build WHERE clause
            where_clauses = ["TRUE"]
            where_params: list = []
            
            if section_no is not None:
                where_clauses.append('"VoterList"."SectionNo" = %s')
                where_params.append(section_no)
            
            if search:
                where_clauses.append('("VoterList"."EName" ILIKE %s OR "VoterList"."VEName" ILIKE %s)')
                where_params.extend([f"%{search}%", f"%{search}%"])

            where_sql = " AND ".join(where_clauses)

            # ✅ NEW: Query with LEFT JOIN to get Mobile from SurveyData
            data_sql = f'''
                SELECT 
                    "VoterList"."VoterID",
                    "VoterList"."PartNo",
                    "VoterList"."SectionNo",
                    "VoterList"."EName",
                    "VoterList"."VEName",
                    "VoterList"."Sex",
                    "VoterList"."Age",
                    "VoterList"."IDCardNo",
                    "VoterList"."VRName" AS "RELATIVE",
                    "VoterList"."Address",
                    "VoterList"."VAddress",
                    {visited_expr} AS "Visited",
                    "SurveyData"."Mobile" AS "Mobile",
                    "SurveyData"."HouseNo" AS "HouseNo"
                FROM "VoterList"
                LEFT JOIN "SurveyData" 
                    ON "VoterList"."VoterID" = "SurveyData"."VoterID"
                    AND "SurveyData"."UserID" = %s
                WHERE {where_sql}
                ORDER BY "VoterList"."VoterID"
                LIMIT %s OFFSET %s
            '''

            # Add main_admin_id to params for the JOIN condition
            data_params = tuple([main_admin_id] + where_params + [limit, offset])

            with conn.cursor() as cur:
                cur.execute(data_sql, data_params)
                rows = cur.fetchall()
                columns = [d[0] for d in cur.description]
                data = [dict(zip(columns, r)) for r in rows]

            # Total count
            count_sql = f'''
                SELECT COUNT(*) 
                FROM "VoterList"
                WHERE {where_sql}
            '''
            with conn.cursor() as c2:
                c2.execute(count_sql, tuple(where_params))
                total = c2.fetchone()[0]

            print(f"✅ /voters: section={section_no}, returned {len(data)}/{total} rows with Mobile")
            
            return {"total": total, "rows": data}
            
    except Exception as e:
        print(f"❌ /voters error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/voters/list")
def get_voter_list(
    search: Optional[str] = None,
    address: Optional[str] = None,
    partno: Optional[str] = None,
    sex: Optional[str] = None,          # Male / Female
    visited: Optional[bool] = None,     # true / false
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    offset: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user)
):
    """
    Paginated & filterable voter list with SurveyData join
    Returns:
    {
        "total": <int>,
        "rows": [ {...}, ... ]
    }
    """
    try:
        # 🔐 User context
        user_id = current_user.get("user_id")
        main_admin_id = current_user.get("main_admin_id") or user_id
        section_no = current_user.get("section_no")

        visited_col = f'Visited_{main_admin_id}'
        visited_expr = f'"VoterList"."{visited_col}"'

        # 🔎 Dynamic filters
        where_clauses = ["TRUE"]
        params: List[Any] = []

        # Section restriction
        where_clauses.append('"VoterList"."SectionNo" = %s')
        params.append(section_no)

        # Search
        if search:
            where_clauses.append(
                '("VoterList"."EName" ILIKE %s OR "VoterList"."VEName" ILIKE %s)'
            )
            params.extend([f"%{search}%", f"%{search}%"])

        # Address
        if address:
            where_clauses.append('"VoterList"."Address" = %s')
            params.append(address)

        # PartNo
        if partno:
            where_clauses.append('"VoterList"."PartNo" = %s')
            params.append(partno)

        # Age filters
        if min_age is not None:
            where_clauses.append('"VoterList"."Age" >= %s')
            params.append(min_age)

        if max_age is not None:
            where_clauses.append('"VoterList"."Age" <= %s')
            params.append(max_age)

        # Sex filter
        if sex:
            sex = sex.lower()
            if sex in ("male", "m"):
                where_clauses.append('"VoterList"."Sex" = %s')
                params.append("M")
            elif sex in ("female", "f"):
                where_clauses.append('"VoterList"."Sex" = %s')
                params.append("F")

        # Visited filter
        if visited is not None:
            where_clauses.append(f'{visited_expr} = %s')
            params.append(visited)

        where_sql = " AND ".join(where_clauses)

        # 📄 DATA QUERY (SurveyData JOIN)
        data_sql = f"""
            SELECT
                "VoterList"."VoterID",
                "VoterList"."PartNo",
                "VoterList"."SectionNo",
                "VoterList"."EName",
                "VoterList"."VEName",
                "VoterList"."Sex",
                "VoterList"."Age",
                "VoterList"."IDCardNo",
                "VoterList"."VPSName",
                "VoterList"."VRName" AS "RELATIVE",
                "VoterList"."Address",
                "VoterList"."VAddress",
                {visited_expr} AS "Visited",
                "SurveyData"."Mobile" AS "Mobile",
                "SurveyData"."HouseNo" AS "HouseNo"
            FROM "VoterList"
            LEFT JOIN "SurveyData"
                ON "VoterList"."VoterID" = "SurveyData"."VoterID"
                AND "SurveyData"."UserID" = %s
            WHERE {where_sql}
            ORDER BY "VoterList"."VoterID"
            LIMIT %s OFFSET %s
        """

        # 🔑 PARAM ORDER IS CRITICAL
        data_params = tuple([main_admin_id] + params + [limit, offset])

        # 🔢 COUNT QUERY
        count_sql = f"""
            SELECT COUNT(*)
            FROM "VoterList"
            WHERE {where_sql}
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                # Data
                cur.execute(data_sql, data_params)
                rows = cur.fetchall()
                columns = [d[0] for d in cur.description]
                data = [dict(zip(columns, r)) for r in rows]

                # Total
                cur.execute(count_sql, tuple(params))
                total = cur.fetchone()[0]

        return {"total": total, "rows": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voters_surname")
def get_voters_by_surname(
    surname: Optional[str] = None,
    offset: int = 0,
    limit: int = 500,
    current_user = Depends(get_current_user)
):

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                # Build WHERE clause
                where_clause = "TRUE"
                params = []
                if surname:
                    where_clause = '"SectionNo" = %s AND "Surname" ILIKE %s'
                    params = [current_user.get("section_no"), f"%{surname}%"]


                # Fetch rows ordered by surname for grouping
                sql = f'''
                    SELECT "VEName", "Surname", "IDCardNo", "Sex" AS "Gender", "Age"
                    FROM "VoterList"
                    WHERE {where_clause}
                    ORDER BY "Surname" ASC, "VEName" ASC
                    LIMIT %s OFFSET %s
                '''
                params.extend([limit, offset])

                cur.execute(sql, params)
                rows = cur.fetchall()
                columns = [d[0] for d in cur.description]

                # Convert rows to dictionary
                raw = [dict(zip(columns, row)) for row in rows]

                # GROUP BY surname
                grouped = {}
                for r in raw:
                    s = r["Surname"].upper().strip()
                    if s not in grouped:
                        grouped[s] = []
                    grouped[s].append({
                        "VEName": r["VEName"],
                        "IDCardNo": r["IDCardNo"],
                        "Gender": r["Gender"],
                        "Age": r["Age"]
                    })

                # Convert to list
                result = [
                    {"surname": s, "members": grouped[s]}
                    for s in sorted(grouped.keys())
                ]

                # Count distinct surnames for pagination
                count_sql = f'''
                    SELECT COUNT(DISTINCT "Surname")
                    FROM "VoterList"
                    WHERE {where_clause}
                '''
                count_params = params[:-2] if surname else []
                cur.execute(count_sql, count_params)
                total = cur.fetchone()[0]

        return {
            "total": int(total),
            "surnames": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voters/filters")
def get_voter_filters(current_user = Depends(get_current_user)):
    """
    Return unique filter lists (addresses, part numbers) and age range.
    Lightweight endpoints that avoid loading entire voter list.
    """
    try:
        section_no = current_user.get("section_no")
        with get_connection() as conn:
            with conn.cursor() as cur:
                if section_no is not None:
                    cur.execute('SELECT DISTINCT "Address" FROM "VoterList" WHERE "SectionNo" = %s', (section_no,))
                else:
                    cur.execute('SELECT DISTINCT "Address" FROM "VoterList"')
                addresses = [r[0] for r in cur.fetchall() if r[0] is not None]

                if section_no is not None:
                    cur.execute('SELECT DISTINCT "PartNo" FROM "VoterList" WHERE "SectionNo" = %s', (section_no,))
                else:
                    cur.execute('SELECT DISTINCT "PartNo" FROM "VoterList"')
                parts = [r[0] for r in cur.fetchall() if r[0] is not None]

                if section_no is not None:
                    cur.execute('SELECT MIN("Age"), MAX("Age") FROM "VoterList" WHERE "SectionNo" = %s', (section_no,))
                else:
                    cur.execute('SELECT MIN("Age"), MAX("Age") FROM "VoterList"')
                min_age, max_age = cur.fetchone()


        return {
            "address_list": sorted(addresses),
            "part_list": sorted(parts),
            "min_age": int(min_age) if min_age is not None else 0,
            "max_age": int(max_age) if max_age is not None else 100
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voters/summary")
def get_voter_summary(current_user = Depends(get_current_user)):
    """
    Returns summary statistics needed for the dashboard:
    - total voters
    - visited count (Visited_<admin_id>)
    - male / female counts
    - top addresses (total, visited, not_visited) limited to top 50 (changeable)
    """
    try:
        main_admin_id = current_user.get("main_admin_id") or current_user.get("user_id")
        visited_col = f'Visited_{main_admin_id}'

        with get_connection() as conn:
            cur = conn.cursor()

            # total
            cur.execute('SELECT COUNT(*) FROM "VoterList"')
            total = cur.fetchone()[0] or 0

            col_exists = True
            if col_exists:
                cur.execute(f'SELECT COUNT(*) FROM "VoterList" WHERE "{visited_col}" = TRUE')
                visited = cur.fetchone()[0] or 0
            else:
                # fallback to generic Visited column if present
                cur.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = %s AND column_name = %s
                """, ("VoterList", "Visited"))

                if cur.fetchone():
                    cur.execute('SELECT COUNT(*) FROM "VoterList" WHERE "Visited" = TRUE')
                    visited = cur.fetchone()[0] or 0
                else:
                    visited = 0

            # sex breakdown
            cur.execute('SELECT "Sex", COUNT(*) FROM "VoterList" GROUP BY "Sex"')
            sex_rows = cur.fetchall()
            sex_breakdown = {r[0]: r[1] for r in sex_rows}

            # top addresses (by total voters) - include visited/not_visited counts
            cur.execute(f'''
                SELECT "Address",
                       COUNT(*) AS total,
                       SUM(CASE WHEN "{visited_col}" = TRUE THEN 1 ELSE 0 END) AS visited,
                       SUM(CASE WHEN "{visited_col}" = FALSE THEN 1 ELSE 0 END) AS not_visited
                FROM "VoterList"
                GROUP BY "Address"
                ORDER BY total DESC
                LIMIT 50
            ''')
            address_rows = cur.fetchall()
            address_chart = []
            for row in address_rows:
                address_chart.append({
                    "Address": row[0],
                    "Total": int(row[1] or 0),
                    "Visited": int(row[2] or 0),
                    "NotVisited": int(row[3] or 0)
                })

        return {
            "total": int(total),
            "visited": int(visited),
            "not_visited": int(total) - int(visited),
            "sex_breakdown": sex_breakdown,
            "address_chart": address_chart
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@app.get("/voters-data")
def get_voters_data(
    view_type: str,  # surname / part_no / address / ward_no / gender
    part_no: Optional[str] = None,
    address: Optional[str] = None,
    surname: Optional[str] = None,
    search: Optional[str] = None,
    gender: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user = Depends(get_current_user)
):
    """
    Fetch voters data grouped by different views.
    Ward data is derived automatically from logged-in user's SectionNo.
    """

    try:
        # ------------------ SECTION SECURITY ------------------
        section_no = current_user.get("section_no")
        if not section_no:
            raise HTTPException(status_code=403, detail="Section not assigned to user")

        where_clauses = ['"SectionNo" = %s']
        params = [section_no]

        # ------------------ FILTERS ------------------
        if surname:
            where_clauses.append('"Surname" ILIKE %s')
            params.append(f"%{surname}%")

        if part_no:
            where_clauses.append('"PartNo" = %s')
            params.append(part_no)

        if address:
            where_clauses.append('"Address" ILIKE %s')
            params.append(f"%{address}%")

        if search:
            where_clauses.append('("EName" ILIKE %s OR "VEName" ILIKE %s)')
            params.extend([f"%{search}%", f"%{search}%"])

        if gender:
            where_clauses.append('"Sex" ILIKE %s')
            params.append(f"%{gender}%")

        where_sql = " AND ".join(where_clauses)

        # ------------------ GROUP CONFIG ------------------
        group_config = {
            "surname": {
                "column": "Surname",
                "order": '"Surname" ASC, "VEName" ASC'
            },
            "part_no": {
                "column": "PartNo",
                "order": '"PartNo" ASC, "VEName" ASC'
            },
            "address": {
                "column": "Address",
                "order": '"Address" ASC, "VEName" ASC'
            },
            "ward_no": {  # ✅ Ward = SectionNo
                "column": "SectionNo",
                "order": '"SectionNo" ASC, "VEName" ASC'
            },
            "gender": {
                "column": "Sex",
                "order": '"Sex" ASC, "VEName" ASC'
            }
        }

        # ------------------ GROUPED VIEW ------------------
        if view_type.lower() in group_config:
            grp = group_config[view_type.lower()]

            sql = f'''
                SELECT
                    "VEName",
                    "{grp["column"]}" AS grp_value,
                    "IDCardNo",
                    "Sex",
                    "Age"
                FROM "VoterList"
                WHERE {where_sql}
                ORDER BY {grp["order"]}
                LIMIT %s OFFSET %s
            '''

            params_page = params + [limit, offset]

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params_page)
                    rows = cur.fetchall()
                    columns = [d[0] for d in cur.description]

                    raw = [dict(zip(columns, r)) for r in rows]

                    grouped = {}
                    for r in raw:
                        # -------- Ward Display Formatting --------
                        if view_type.lower() == "ward_no":
                            key = f"Ward {r['grp_value']}"
                        else:
                            key = str(r["grp_value"]) if r["grp_value"] else "UNKNOWN"
                            key = key.strip().upper()

                        grouped.setdefault(key, []).append({
                            "VEName": r["VEName"],
                            "IDCardNo": r["IDCardNo"],
                            "Gender": r["Sex"],
                            "Age": r["Age"]
                        })

                    result = [
                        {"group": k, "members": grouped[k]}
                        for k in sorted(grouped.keys())
                    ]

                    # -------- Total Groups Count --------
                    count_sql = f'''
                        SELECT COUNT(DISTINCT "{grp["column"]}")
                        FROM "VoterList"
                        WHERE {where_sql}
                    '''
                    cur.execute(count_sql, tuple(params))
                    total = cur.fetchone()[0]

            return {
                "type": view_type.lower(),
                "status": True,
                "section": section_no,
                "total_groups": int(total),
                "data": result
            }

        # ------------------ INVALID VIEW ------------------
        return {
            "type": view_type.lower(),
            "status": False,
            "message": "Invalid or unsupported view type"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# # -------------------- SUBMIT SURVEY (kept logic but hardened) --------------------
@app.post("/submit-survey", response_model=SurveySubmissionResponse)
def submit_survey(
    request: SurveySubmissionRequest,
    current_user = Depends(get_current_user)
):
    """Submit survey form data and mark voters as visited."""
    try:
        main_admin_id = (
            request.main_admin_id
            or current_user.get("main_admin_id")
            or current_user.get("user_id")
        )
        section_no = current_user.get("section_no")

        with get_connection() as conn:
            with conn.cursor() as cur:

                # ------------------ FAMILY HEAD ------------------
                cur.execute("""
                    SELECT "EName", "VEName", "SectionNo", "Sex", "Age",
                           "VAddress", "PartNo"
                    FROM "VoterList"
                    WHERE "VoterID" = %s
                """, (request.family_head_id,))

                head_row = cur.fetchone()
                if not head_row:
                    raise HTTPException(
                        status_code=404,
                        detail="Family head not found"
                    )

                head = dict(zip([d[0] for d in cur.description], head_row))

                if section_no is not None and head["SectionNo"] != section_no:
                    raise HTTPException(
                        status_code=403,
                        detail="Family head does not belong to your Section"
                    )

                # ------------------ FAMILY COUNTS ------------------
                if request.selected_family_ids:
                    placeholders = ",".join(["%s"] * len(request.selected_family_ids))
                    cur.execute(
                        f'''
                        SELECT "Sex"
                        FROM "VoterList"
                        WHERE "VoterID" IN ({placeholders})
                        ''',
                        request.selected_family_ids
                    )
                    fam_rows = cur.fetchall()
                    family_members = [
                        dict(zip([d[0] for d in cur.description], r))
                        for r in fam_rows
                    ]

                    male_count = len(
                        [m for m in family_members if m["Sex"] in ("M", "Male")]
                    )
                    female_count = len(
                        [m for m in family_members if m["Sex"] in ("F", "Female")]
                    )
                    total_voters = len(family_members)
                else:
                    male_count = female_count = total_voters = 0

                # ------------------ SURVEY INSERT ------------------
                head_choice = f'{head["EName"]} ({head["VEName"]}) - {request.house_number}'

                cur.execute("""
                    INSERT INTO "SurveyData"
                    ("VoterID", "VEName", "HouseNo", "Landmark", "VAddress",
                     "Mobile", "SectionNo", "VotersCount", "Male", "Female",
                     "Caste", "Sex", "PartNo", "Age", "UserID")
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING "SurveyNo"
                """, (
                    request.family_head_id,
                    head_choice,
                    request.house_number,
                    request.landmark,
                    head["VAddress"],
                    request.mobile,
                    head["SectionNo"],
                    total_voters,
                    male_count,
                    female_count,
                    request.caste,
                    head["Sex"],
                    str(head["PartNo"]),
                    head["Age"],
                    main_admin_id
                ))

                survey_id = cur.fetchone()[0]

                # ------------------ VISITED UPDATE (FIXED) ------------------
                if request.selected_family_ids:
                    visited_col = f'Visited_{main_admin_id}'
                        
                    placeholders = ",".join(["%s"] * len(request.selected_family_ids))

                    query = f'''
                        UPDATE "VoterList"
                        SET "{visited_col}" = %s
                        WHERE "VoterID" IN ({placeholders})
                    '''

                    cur.execute(
                        query,
                        [bool(request.visited)] + request.selected_family_ids
                    )

                conn.commit()

        return SurveySubmissionResponse(
            success=True,
            message="Survey submitted successfully",
            survey_id=survey_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting survey: {str(e)}"
        )


@app.get("/surveys")
def get_surveys(limit: int = 500, offset: int = 0, current_user = Depends(get_current_user)):
    """Return survey data for the current user's admin (paginated).

    Returns JSON: {"total": <int>, "rows": [ ... ]}
    """
    try:
        user_id = current_user.get("main_admin_id") or current_user.get("user_id")
        with get_connection() as conn:
            with conn.cursor() as cur:
                sql = '''
                    SELECT "SurveyNo","VoterID","VEName","Sex","HouseNo","Landmark","VAddress","Mobile","PartNo","SectionNo","VotersCount","Male","Female","Caste","Submission_Time","Age"
                    FROM "SurveyData"
                    WHERE "UserID" = %s
                    ORDER BY "SurveyNo"
                    LIMIT %s OFFSET %s
                '''
                cur.execute(sql, (user_id, limit, offset))
                rows = cur.fetchall()
                columns = [d[0] for d in cur.description]
                data = [dict(zip(columns, r)) for r in rows]

                # total
                cur.execute('SELECT COUNT(*) FROM "SurveyData" WHERE "UserID" = %s', (user_id,))
                total = cur.fetchone()[0]

                return {"total": total, "rows": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== RUN ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
# ==================== RUN ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


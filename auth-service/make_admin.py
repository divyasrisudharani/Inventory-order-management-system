from app.database import SessionLocal
from app.models import User

db = SessionLocal()

try:
    email = input("Enter the registered user email: ").strip().lower()

    user = db.query(User).filter(User.email == email).first()

    if user is None:
        print("User not found. Check the email.")
    else:
        user.role = "administrator"
        db.commit()
        db.refresh(user)

        print("Administrator role assigned successfully!")
        print("User ID:", user.id)
        print("Email:", user.email)
        print("Role:", user.role)

except Exception as e:
    db.rollback()
    print("Error:", e)

finally:
    db.close()
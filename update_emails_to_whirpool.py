"""Update existing user emails from @example.com to @whirpool.com.

Run once to migrate seed data after introducing the @whirpool.com SSO rule.
Preserves all foreign-key relationships — only updates the email column.
"""

from sqlalchemy import update

from src.db.session import SessionLocal
from src.db.models.learning_platform import User


OLD_DOMAIN = "@example.com"
NEW_DOMAIN = "@whirpool.com"


def main() -> None:
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.email.like(f"%{OLD_DOMAIN}")).all()
        if not users:
            print(f"No users with {OLD_DOMAIN} found. Nothing to update.")
            return

        print(f"Found {len(users)} users to migrate:")
        for u in users:
            new_email = u.email.replace(OLD_DOMAIN, NEW_DOMAIN)
            print(f"  {u.email}  ->  {new_email}")
            u.email = new_email

        db.commit()
        print(f"\nUpdated {len(users)} users successfully.")
    except Exception as exc:
        db.rollback()
        print(f"Error: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

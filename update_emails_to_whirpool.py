"""Update existing user emails to @whirlpool.com.

Originally migrated @example.com → @whirpool.com; now also corrects the
typo'd @whirpool.com → @whirlpool.com so the SSO domain matches the
corporate brand. Preserves all foreign-key relationships — only updates
the email column.
"""

from src.db.session import SessionLocal
from src.db.models.learning_platform import User


OLD_DOMAINS = ["@example.com", "@whirpool.com"]
NEW_DOMAIN = "@whirlpool.com"


def main() -> None:
    db = SessionLocal()
    try:
        users: list[User] = []
        for old in OLD_DOMAINS:
            users.extend(db.query(User).filter(User.email.like(f"%{old}")).all())

        if not users:
            print(f"No users with {OLD_DOMAINS} found. Nothing to update.")
            return

        print(f"Found {len(users)} users to migrate:")
        for u in users:
            new_email = u.email
            for old in OLD_DOMAINS:
                if new_email.endswith(old):
                    new_email = new_email[: -len(old)] + NEW_DOMAIN
                    break
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

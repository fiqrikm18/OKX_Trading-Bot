from src.infrastructure.persistence.postgres_repo import PostgresRepository
import getpass


def main():
    print("🔐 Create Dashboard Admin User")
    username = input("Enter Username: ")
    password = getpass.getpass("Enter Password: ")
    confirm = getpass.getpass("Confirm Password: ")

    if password != confirm:
        print("❌ Passwords do not match!")
        return

    try:
        repo = PostgresRepository()
        repo.create_user(username, password)
        print(f"✅ User '{username}' created successfully!")
    except Exception as e:
        print(f"❌ Error creating user: {e}")


if __name__ == "__main__":
    main()

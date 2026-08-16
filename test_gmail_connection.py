from app.tools.gmail import get_gmail_service
from app.tools.gmail_parser import parse_gmail_message


def main():

    service = get_gmail_service()

    response = (
        service
        .users()
        .messages()
        .list(
            userId="me",
            q="is:unread",
            maxResults=5
        )
        .execute()
    )

    messages = response.get("messages", [])

    print(f"\nFound {len(messages)} unread message(s).\n")

    for message in messages:

        message_id = message["id"]

        full_message = (
            service
            .users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="full"
            )
            .execute()
        )

        parsed = parse_gmail_message(full_message)

        print("----------------------------------------")
        print(f"Message ID: {parsed['message_id']}")
        print(f"Name:       {parsed['name']}")
        print(f"Email:      {parsed['email']}")
        print(f"Subject:    {parsed['subject']}")

        print("\nBody:")
        print(parsed["body"][:500])

        print()


if __name__ == "__main__":
    main()
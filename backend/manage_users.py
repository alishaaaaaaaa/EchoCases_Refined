"""
Manage EchoCases user accounts from the command line.

There is no public sign-up: accounts are created here (or by an admin through
the API). Passwords are typed at a hidden prompt, never passed as arguments,
so they don't end up in shell history.

Usage (from backend/):
    python manage_users.py create <username> --role admin
    python manage_users.py create <username> --role investigator
    python manage_users.py list
    python manage_users.py set-password <username>
    python manage_users.py set-role <username> admin|investigator
    python manage_users.py deactivate <username>
    python manage_users.py activate <username>
"""

import argparse
import getpass
import sys

from dotenv import load_dotenv

load_dotenv()

import auth  # noqa: E402  (load .env first so ECHOCASES_DB is honoured)


def prompt_password():
    first = getpass.getpass("Password: ")
    if first != getpass.getpass("Confirm password: "):
        raise ValueError("Passwords do not match.")
    return first


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="create a user")
    create.add_argument("username")
    create.add_argument("--role", choices=auth.ROLES, default="investigator")

    sub.add_parser("list", help="list users")

    pw = sub.add_parser("set-password", help="reset a user's password (signs them out)")
    pw.add_argument("username")

    role = sub.add_parser("set-role", help="change a user's role")
    role.add_argument("username")
    role.add_argument("role", choices=auth.ROLES)

    for name in ("deactivate", "activate"):
        p = sub.add_parser(name, help=f"{name} a user")
        p.add_argument("username")

    args = ap.parse_args()
    auth.init_db()

    try:
        if args.command == "create":
            auth.create_user(args.username, prompt_password(), args.role)
            print(f"Created {args.role} '{args.username}'.")
        elif args.command == "list":
            users = auth.list_users()
            if not users:
                print("No users yet. Create an admin with: python manage_users.py create <name> --role admin")
            for u in users:
                status = "active" if u["active"] else "deactivated"
                print(f"{u['username']:<24} {u['role']:<13} {status:<12} created {u['created_at']}")
        elif args.command == "set-password":
            auth.set_password(args.username, prompt_password())
            print(f"Password updated for '{args.username}'. Their existing sessions are signed out.")
        elif args.command == "set-role":
            auth.set_role(args.username, args.role)
            print(f"'{args.username}' is now {args.role}.")
        elif args.command in ("deactivate", "activate"):
            auth.set_active(args.username, args.command == "activate")
            print(f"'{args.username}' {args.command}d.")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

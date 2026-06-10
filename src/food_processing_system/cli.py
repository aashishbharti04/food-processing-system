"""Command-line interface.

Re-implements the original menu-driven flow — register / log in / exit, then the
six in-account actions (view customers, update details, exit, order food, view
orders, rate us) — on top of the new layered architecture, with validation,
error handling and a themed UI.
"""

from __future__ import annotations

import sys

from .config import AppConfig
from .database import Database, DatabaseError
from .models import Customer
from .repositories import CustomerRepository, OrderRepository, RatingRepository
from .services import (
    AuthenticationError,
    CustomerService,
    OrderService,
    RatingService,
    ServiceError,
)
from .ui import Console


class App:
    """Wires together the services and drives the interactive menus."""

    def __init__(self, db: Database, console: Console) -> None:
        self.console = console
        customers = CustomerRepository(db)
        orders = OrderRepository(db)
        ratings = RatingRepository(db)
        self.customers = CustomerService(customers, orders, ratings)
        self.orders = OrderService(orders)
        self.ratings = RatingService(ratings)

    # -- Input helpers --------------------------------------------------- #

    def _prompt(self, label: str) -> str:
        """Read a line of text input."""
        return input(f"  {label}: ").strip()

    def _prompt_int(self, label: str) -> int:
        """Read an integer, re-prompting on invalid input instead of crashing."""
        while True:
            raw = self._prompt(label)
            try:
                return int(raw)
            except ValueError:
                self.console.error("Please enter a whole number.")

    # -- Top-level menu -------------------------------------------------- #

    def run(self) -> None:
        """Run the main entry menu."""
        self.console.banner("ORDER YOUR FOOD HERE", "Food Processing System")
        self.console.print()
        self.console.print("  1. Create your account")
        self.console.print("  2. Log in")
        self.console.print("  3. Exit")
        self.console.print()

        choice = self._prompt_int("Enter your choice")
        if choice == 1:
            self._register()
        elif choice == 2:
            self._login()
        elif choice == 3:
            self.console.info("Thank you for visiting!")
        else:
            self.console.error("Invalid choice.")

        self.console.footer()

    # -- Registration ---------------------------------------------------- #

    def _register(self) -> None:
        self.console.heading("Create your account")
        name = self._prompt("Enter your name")
        account_no = self._prompt_int("Choose an account number")
        address = self._prompt("Enter your address")
        password = self._prompt("Choose a password")
        try:
            self.customers.register(name, account_no, address, password)
            self.console.success("Account created.")
        except ServiceError as exc:
            self.console.error(str(exc))

    # -- Login ----------------------------------------------------------- #

    def _login(self) -> None:
        self.console.heading("Log in")
        self.console.info("Fill in your details to continue.")
        name = self._prompt("Enter your name")
        account_no = self._prompt_int("Enter your account number")
        password = self._prompt("Enter your password")
        try:
            customer = self.customers.authenticate(name, account_no, password)
        except AuthenticationError as exc:
            self.console.error(str(exc))
            return

        self.console.success(f"Welcome to your food service, {customer.name}!")
        self._account_menu(customer)

    # -- In-account menu ------------------------------------------------- #

    def _account_menu(self, customer: Customer) -> None:
        self.console.heading("What would you like to do?")
        self.console.print("  1. See customer details")
        self.console.print("  2. Update your details")
        self.console.print("  3. Exit")
        self.console.print("  4. Order food")
        self.console.print("  5. See ordered food")
        self.console.print("  6. Rate us")
        self.console.print()

        action = self._prompt_int("Enter your choice")
        handlers = {
            1: self._view_customers,
            2: lambda: self._update_details(customer),
            3: self._exit,
            4: lambda: self._order_food(customer),
            5: self._view_orders,
            6: lambda: self._rate(customer),
        }
        handler = handlers.get(action)
        if handler is None:
            self.console.error("Error — invalid choice.")
            return
        handler()

    def _view_customers(self) -> None:
        self.console.heading("Customer details")
        with self.console.spinner("Loading customers"):
            customers = self.customers.all_customers()
        if not customers:
            self.console.empty_state("No customers registered yet")
            return
        self.console.info(f"Total customers: {len(customers)}")
        self.console.table(
            ["Account No", "Name", "Address"],
            [[c.account_no, c.name, c.address] for c in customers],
        )
        self.console.info("Visit again!")

    def _update_details(self, customer: Customer) -> None:
        self.console.heading("Update your details")
        name = self._prompt("Enter name")
        address = self._prompt("Enter address")
        try:
            self.customers.update_details(customer.account_no, name, address)
            self.console.success("Your details were successfully updated.")
        except ServiceError as exc:
            self.console.error(str(exc))

    def _exit(self) -> None:
        self.console.info("Thank you for visiting!")

    def _order_food(self, customer: Customer) -> None:
        self.console.heading("Order food")
        food_name = self._prompt("Enter the name of the food")
        price = self._prompt("Enter the cost of your food")
        address = self._prompt("Enter your address")
        try:
            with self.console.spinner("Placing your order"):
                self.orders.place_order(
                    food_name=food_name,
                    price=price,
                    address=address,
                    customer_name=customer.name,
                    account_no=customer.account_no,
                )
            self.console.success("Successfully ordered.")
        except ServiceError as exc:
            self.console.error(str(exc))

    def _view_orders(self) -> None:
        self.console.heading("Ordered food")
        with self.console.spinner("Loading orders"):
            orders = self.orders.all_orders()
        if not orders:
            self.console.empty_state("No orders placed yet")
            return
        self.console.info(f"Total orders: {len(orders)}")
        self.console.table(
            ["ID", "Food", "Price", "Customer", "Account No"],
            [
                [o.id, o.food_name, o.price, o.customer_name, o.account_no]
                for o in orders
            ],
        )
        self.console.info("Visit again!")

    def _rate(self, customer: Customer) -> None:
        self.console.heading("Rate us for your service")
        score = self._prompt_int("Enter your rating (1-5)")
        try:
            self.ratings.rate(customer.account_no, score)
            self.console.success("Thanks for rating!")
        except ServiceError as exc:
            self.console.error(str(exc))


def main(argv: list[str] | None = None) -> int:
    """Application entry point. Returns a process exit code."""
    config = AppConfig.from_env()
    console = Console(use_colors=config.use_colors)
    try:
        with Database.connect(config.database) as db:
            db.init_schema()
            console.success(f"Successfully connected ({config.database.backend}).")
            App(db, console).run()
    except DatabaseError as exc:
        console.error(f"Database error: {exc}")
        return 1
    except (KeyboardInterrupt, EOFError):
        console.print()
        console.info("Goodbye!")
        return 0
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

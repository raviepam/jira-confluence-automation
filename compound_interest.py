import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def parse_decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise argparse.ArgumentTypeError("Enter a valid number.") from error


def calculate_compound_interest(
    principal: Decimal,
    annual_rate_percent: Decimal,
    months: int,
) -> tuple[Decimal, Decimal]:
    if principal <= 0:
        raise ValueError("Principal must be greater than zero.")
    if annual_rate_percent < 0:
        raise ValueError("Annual rate cannot be negative.")
    if months < 0:
        raise ValueError("Number of months cannot be negative.")

    monthly_rate = annual_rate_percent / Decimal("1200")
    amount = principal * (Decimal("1") + monthly_rate) ** months
    return amount, amount - principal


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate interest compounded monthly."
    )
    parser.add_argument("--principal", type=parse_decimal, default=Decimal("15847"))
    parser.add_argument("--annual-rate", type=parse_decimal, default=Decimal("7.34"))
    parser.add_argument("--years", type=int, default=8)
    parser.add_argument("--months", type=int, default=7)
    args = parser.parse_args()
    total_months = args.years * 12 + args.months

    try:
        amount, interest = calculate_compound_interest(
            args.principal,
            args.annual_rate,
            total_months,
        )
    except ValueError as error:
        parser.error(str(error))

    cent = Decimal("0.01")
    print(f"Final amount: ${amount.quantize(cent, rounding=ROUND_HALF_UP):,.2f}")
    print(f"Total interest: ${interest.quantize(cent, rounding=ROUND_HALF_UP):,.2f}")


if __name__ == "__main__":
    main()
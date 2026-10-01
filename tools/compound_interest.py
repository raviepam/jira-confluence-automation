import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext


def parse_decimal(value: str) -> Decimal:
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise argparse.ArgumentTypeError("Enter a valid number.") from error

    if not number.is_finite():
        raise argparse.ArgumentTypeError("Enter a finite number.")
    return number


def calculate_compound_interest(
    principal: Decimal,
    annual_rate_percent: Decimal,
    compounds_per_year: int,
    years: Decimal,
) -> tuple[Decimal, Decimal]:
    if principal <= 0:
        raise ValueError("Principal must be greater than zero.")
    if annual_rate_percent < 0:
        raise ValueError("Annual rate cannot be negative.")
    if compounds_per_year <= 0:
        raise ValueError("Compounds per year must be greater than zero.")
    if years < 0:
        raise ValueError("Total years cannot be negative.")

    periodic_rate = annual_rate_percent / Decimal(100 * compounds_per_year)
    total_periods = Decimal(compounds_per_year) * years
    amount = principal * (Decimal(1) + periodic_rate) ** total_periods
    return amount, amount - principal


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate compound interest for a given compounding frequency."
    )
    parser.add_argument("principal", type=parse_decimal, help="starting principal")
    parser.add_argument(
        "annual_rate",
        type=parse_decimal,
        help="annual interest rate as a percentage, such as 7.34",
    )
    parser.add_argument(
        "compounds_per_year",
        type=int,
        help="number of compounding periods per year, such as 12 for monthly",
    )
    parser.add_argument(
        "years",
        type=parse_decimal,
        help="total duration in years; fractional years are supported",
    )
    args = parser.parse_args()

    try:
        with localcontext() as context:
            context.prec = 50
            amount, interest = calculate_compound_interest(
                args.principal,
                args.annual_rate,
                args.compounds_per_year,
                args.years,
            )
    except ValueError as error:
        parser.error(str(error))

    cents = Decimal("0.01")
    rounded_amount = amount.quantize(cents, rounding=ROUND_HALF_UP)
    rounded_interest = interest.quantize(cents, rounding=ROUND_HALF_UP)
    print(f"Final amount: {rounded_amount:,.2f}")
    print(f"Interest earned: {rounded_interest:,.2f}")


if __name__ == "__main__":
    main()

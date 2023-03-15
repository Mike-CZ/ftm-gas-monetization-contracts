from dataclasses import dataclass

WITHDRAWAL_EPOCHS_LIMIT = 10
# withdrawal confirmation must not be greater than number of data providers created in conftest.py
WITHDRAWAL_CONFIRMATION = 3

@dataclass(frozen=True)
class ProjectParams:
    project_id: int = 1
    metadata_uri: str = "some-uri"
    contracts = [
        '0x8d6E92cff3E20f81C316CC09F97b77308dfc1EC5',
        '0x6ecA1cC848c80936Bb3FECA348A82b51ca777067',
        '0xCBA8bc188B3a0Ce2bA67bA40A4B1740D17aBc292'
    ]
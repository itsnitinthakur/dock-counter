"""Estimate how many units were loaded or unloaded from weights.

Truck method: weigh the vehicle on the weighbridge when it arrives and when it
leaves; the difference is the goods. Platform method: weigh each pallet.
"""


def estimate_units(gross_kg, tare_kg, unit_kg, packing_kg=0.0):
    """Units = (gross - tare - packing) / weight of one unit. Returns (units, net_kg)."""
    if unit_kg <= 0:
        raise ValueError("unit weight must be positive")
    net = gross_kg - tare_kg - packing_kg
    if net < 0:
        raise ValueError("net weight is negative: check the readings")
    return round(net / unit_kg), net


if __name__ == "__main__":
    # Example: truck 14,250 kg loaded, 9,180 kg empty, 50 kg bags, 40 kg of pallets.
    units, net = estimate_units(14250, 9180, 50, packing_kg=40)
    print(f"Net goods {net:.0f} kg, about {units} bags")

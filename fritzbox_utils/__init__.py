import re
import hashlib
import tabulate
import keyring

import pandas as pd
import matplotlib.pyplot as plt

from getpass import getpass

# from sqlalchemy import create_engine
from pathlib import Path
from io import StringIO
from fritzconnection import FritzConnection

pd.set_option("display.max_rows", 500)

keyring_id = "fritzbox_admin_password"


def check_status():
    if (
        passwd := keyring.get_password(service_name=keyring_id, username="admin")
    ) is None:
        print("Enter FritzBox password below:")
        passwd = getpass()
        keyring.set_password(
            service_name=keyring_id,
            username="admin",
            password=passwd,
        )
        print("Password successfully saved to the system keyring.")

    fc = FritzConnection(address="192.168.0.1", password=passwd)

    log = fc.call_action("DeviceInfo1", "GetDeviceLog")["NewDeviceLog"]

    ldf = pd.DataFrame(
        re.findall(r"(\d\d\.\d\d.\d\d \d\d:\d\d:\d\d) (.*)", log),
        columns=["timestamp", "text"],
    )
    ldf["timestamp"] = pd.to_datetime(ldf["timestamp"], format="%d.%m.%y %H:%M:%S")

    ldf.loc[ldf["text"].str.contains("Training"), "event"] = "training"
    ldf.loc[
        ldf["text"].str.contains("Internetverbindung wurde erfolgreich hergestellt."),
        "event",
    ] = "internet connected"
    ldf.loc[
        ldf["text"].str.contains(
            "Internetverbindung \(Telefonie\) wurde erfolgreich hergestellt."
        ),
        "event",
    ] = "internet phone connected"
    ldf.loc[
        ldf["text"].str.contains("IPv6-Präfix wurde erfolgreich bezogen."), "event"
    ] = "ipv6 prefix"
    ldf.loc[
        ldf["text"].str.contains(
            "Internetverbindung IPv6 wurde erfolgreich hergestellt."
        ),
        "event",
    ] = "internet ipv6 connected"
    ldf.loc[ldf["text"].str.contains("DSL ist verfügbar"), "event"] = "dsl available"
    ldf.loc[
        ldf["text"].str.contains("Internetverbindung wurde getrennt."), "event"
    ] = "internet connection interrupted"
    ldf.loc[
        ldf["text"].str.contains("Zeitüberschreitung bei der PPP-Aushandlung."), "event"
    ] = "ppp timeout"
    ldf.loc[
        ldf["text"].str.contains("Internetverbindung IPv6 wurde getrennt"), "event"
    ] = "internet ipv6 connection interrupted"
    ldf.loc[
        ldf["text"].str.contains("Internetverbindung \(Telefonie\) wurde getrennt"),
        "event",
    ] = "internet phone connection interrupted"
    ldf.loc[ldf["text"].str.contains("DSL antwortet nicht"), "event"] = "dsl no answer"
    ldf.loc[
        ldf["text"].str.contains("IPv6-Präfix wurde erfolgreich aktualisiert"), "event"
    ] = "updated ipv6 prefix"
    ldf.loc[
        ldf["text"].str.contains(
            "WLAN-Übertragungsqualität durch reduzierte Kanalbandbreite erhöht"
        ),
        "event",
    ] = "improved wifi quality"
    ldf.loc[
        ldf["text"].str.contains(
            "Die Internetverbindung wird kurz unterbrochen, "
            "um der Zwangstrennung durch den Anbieter zuvorzukommen."
        ),
        "event",
    ] = "internet connection short interruption"

    ldf = ldf.sort_values("timestamp").reset_index(drop=True)

    ldf["hash"] = ldf.apply(
        lambda r: hashlib.sha256(
            str.encode(f"{r['timestamp']!r}{r['text']!r}")
        ).hexdigest()[:15],
        axis=1,
    )
    ldf.set_index(["timestamp", "hash"], inplace=True)

    df = pd.read_csv("/home/jung/fritzbox.csv", parse_dates=[0])
    df.set_index(["timestamp", "hash"], inplace=True)

    sd = list(set(ldf.index) - set(df.index))
    if sd:
        new_events = ldf.loc[sd].sort_values(["timestamp", "hash"])
        print("New events:")
        print(new_events)

        ldf = df.append(new_events).reset_index()
        ldf.to_csv("/home/jung/fritzbox.csv", index=False)
    else:
        print("No new events")

    ldf.reset_index(inplace=True)
    outages = (
        ldf.groupby(["event", ldf["timestamp"].dt.date])
        .count()
        .loc["internet connection interrupted"]["timestamp"]
        .rename("outages")
    )

    print(
        tabulate.tabulate(
            pd.DataFrame(outages).rename({"timestamp": "date"}, axis=1),
            headers="keys",
            tablefmt="psql",
        )
    )
    # (ldf.groupby(["event", ldf["timestamp"].dt.date]).count().loc[
    #     "internet connection interrupted"
    # ]["timestamp"]).hist()
    # plt.show()

    # ldf[ldf["event"] == "internet connection interrupted"]

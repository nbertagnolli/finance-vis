from typing import List
import sys

import dill
import gspread
import matplotlib.pyplot as plt
import numpy as np
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import seaborn as sns
import streamlit as st

sns.set()


@st.cache
def load_data_from_gdrive():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "/Users/tetracycline/Documents/Cred/finances-d3465a127683.json", scope
    )

    gc = gspread.authorize(credentials)

    worksheet = gc.open("Finances")
    data = {}
    for w in worksheet.worksheets():
        temp_data = w.get_all_values()
        headers = temp_data.pop(0)
        data[w._properties["title"]] = pd.DataFrame(temp_data, columns=headers)

    return data


def main():
    st.title("Finance Explorer")
    data = load_data_from_gdrive()

    # Plot Historical Spending
    categories = st.multiselect(
        "Category", sorted(list(set(data["Historical_Spending"].columns)))
    )
    figure, ax = plt.subplots(figsize=(15, 8), dpi=80, facecolor="w", edgecolor="k")
    data["Historical_Spending"][categories].astype("float").plot(ax=ax)
    ax.set_xticks(range(0, len(data["Historical_Spending"]["Date"])))
    ax.set_xticklabels(data["Historical_Spending"]["Date"], rotation=90)
    ax.set_title(
        "Historical  " + ", ".join(categories),
        fontdict={"fontsize": 33, "fontweight": "medium"},
    )
    st.show(figure)

    # Plot Savings
    # savings_categories = st.multiselect("Category", sorted(list(set(data["Savings Totals"].columns))))
    savings_totals = data["Savings Totals"][
        ["401k", "Roth IRA", "GESPP", "Vangaurd", "HSA", "CD"]
    ].astype("float")
    savings_totals["sum"] = savings_totals.apply(
        lambda row: row["401k"] + row["Roth IRA"] + row["GESPP"] + row["Vangaurd"],
        axis=1,
    )
    figure, ax = plt.subplots(figsize=(15, 8), dpi=80, facecolor="w", edgecolor="k")
    savings_totals.tail(-1).plot(ax=ax)
    ax.set_xticks(range(0, len(data["Savings Totals"]["Date"])))
    ax.set_xticklabels(data["Savings Totals"]["Date"], rotation=90)
    ax.set_title(
        "Historical  Savings", fontdict={"fontsize": 33, "fontweight": "medium"}
    )
    st.show(figure)

    # Plot Savings Over Time / With future predictions
    figure, ax = plt.subplots(figsize=(15, 8), dpi=80, facecolor="w", edgecolor="k")
    data["Savings Totals"][["Total"]].astype("float").plot(ax=ax)
    ax.set_title("Total Savings")
    ax.set_xlabel("time")
    ax.set_ylabel("$")
    st.show(figure)

    # Add Total yearly spending
    expenditures = data["Expenditures"]
    expenditures["Timestamp"] = pd.to_datetime(data["Expenditures"]["Timestamp"])
    expenditures["year"] = expenditures["Timestamp"].apply(lambda x: x.year)
    expenditures["month"] = expenditures["Timestamp"].apply(lambda x: x.month)
    expenditures["Amount"] = expenditures["Amount"].astype("float")
    figure, ax = plt.subplots(figsize=(15, 8), dpi=80, facecolor="w", edgecolor="k")
    expenditures.groupby("year").agg("sum").plot.bar(ax=ax)
    ax.set_xlabel("year")
    ax.set_ylabel("$")
    ax.set_title("Yearly Spending")
    st.show(figure)

    # Total Spending by Category
    figure, ax = plt.subplots(figsize=(15, 8), dpi=80, facecolor="w", edgecolor="k")
    expenditures.groupby("Categories").agg("sum")["Amount"].sort_values(
        ascending=False
    ).plot.bar()

    ax.set_xlabel("Category")
    ax.set_ylabel("$")
    ax.set_title("Yearly Spending By Category")
    st.show(figure)

    # Add Total monthly by category
    figure, ax = plt.subplots(figsize=(15, 8), dpi=80, facecolor="w", edgecolor="k")
    category_groups = (
        expenditures.groupby(["Categories", "year"]).agg("sum").reset_index()
    )
    g = sns.catplot(
        x="Categories",
        y="Amount",
        hue="year",
        data=category_groups,
        kind="bar",
        height=4,
        aspect=0.7,
        ax=ax,
    )
    st.show(figure)

    # Add average monthly by category
    figure, ax = plt.subplots(figsize=(15, 8), dpi=80, facecolor="w", edgecolor="k")

    category_groups = (
        expenditures[expenditures["Categories"] != "xxx"]
        .groupby(["Categories", "month"])
        .agg(np.mean)
        .reset_index()
    )

    g = sns.catplot(
        x="Categories",
        y="Amount",
        hue="month",
        data=category_groups,
        kind="bar",
        height=4,
        aspect=0.7,
        ax=ax,
    )
    st.show(figure)

    # Yearly cost by vendor
    figure, ax = plt.subplots(figsize=(15, 8), dpi=80, facecolor="w", edgecolor="k")
    expenditures.groupby("Vendor").agg("sum")["Amount"].sort_values(
        ascending=False
    ).head(20).plot.bar(ax=ax)
    ax.set_title("Total Cost by Vendor")
    ax.set_ylabel("$")
    ax.set_xlabel("Vendor")
    st.show(figure)

    # Most expensive purchases
    figure, ax = plt.subplots(figsize=(15, 8), dpi=80, facecolor="w", edgecolor="k")
    expenditures.groupby("Description").agg("sum")["Amount"].sort_values(
        ascending=False
    ).head(20).plot.bar(ax=ax)
    ax.set_title("Most Expensive Purchases")
    ax.set_ylabel("$")
    ax.set_xlabel("Purchase")
    st.show(figure)


if __name__ == "__main__":
    main()

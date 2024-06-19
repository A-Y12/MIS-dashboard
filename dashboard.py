import streamlit as st
import plotly.express as px
import pandas as pd
import os
import warnings

warnings.filterwarnings('ignore')

st.set_page_config(page_title="MIS Dashboard", page_icon=":bar_chart:", layout="wide")

# Custom CSS for animations and styling
st.markdown(
    """
    <style>
    .stApp {
        padding-top: 4rem;
    }
    .block-container {
        padding-top: 2rem;
        transition: transform 0.3s ease-in-out;
    }
    .block-container:hover {
        transform: scale(1.02);
    }
    .sidebar .sidebar-content {
        transition: transform 0.3s ease-in-out;
    }
    .sidebar .sidebar-content:hover {
        transform: scale(1.02);
    }
    .animated-header {
        animation: fadeInDown 1s ease-in-out;
    }
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title(":bar_chart: MIS Dashboard", anchor="animated-header")

# File uploader
fl = st.file_uploader(":file_folder: Upload a file", type=(["csv", "xlsx", "xls"]))
if fl is not None:
    filename = fl.name
    st.write(filename)
    if filename.endswith('.csv'):
        df = pd.read_csv(fl, encoding="ISO-8859-1")
    else:
        df = pd.read_excel(fl)

    # Display column names for debugging
    #st.write("Columns in the uploaded file:", df.columns.tolist())

    # Convert date columns to datetime
    date_columns = ["PR Approved Date", "PR Clarification date", "Released by Buyer", "Released by A1",
                    "Released by A2", "Released by Management", "Released by Finance", "Invoice Date",
                    "Invoice Received Date", "GRN date", "Inventory sheet updated date", "Advance Payment Date",
                    "Balance payment Date", "GST payment date", "Expected delivery date", "Actual delivery date"]

    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Filter data based on date range
    col1, col2 = st.columns((2))
    startDate = df["PR Approved Date"].min() if "PR Approved Date" in df.columns else df["Invoice Date"].min()
    endDate = df["PR Approved Date"].max() if "PR Approved Date" in df.columns else df["Invoice Date"].max()

    with col1:
        date1 = st.date_input("Start Date", startDate)

    with col2:
        date2 = st.date_input("End Date", endDate)

    date_column = "PR Approved Date" if "PR Approved Date" in df.columns else "Invoice Date"
    df = df[(df[date_column] >= pd.to_datetime(date1)) & (df[date_column] <= pd.to_datetime(date2))].copy()

    st.sidebar.header("Choose your filter:")
    # Create filters for columns
    vendor_status = st.sidebar.multiselect("Pick Vendor Status", df["Vendor name"].unique())
    urgent_planned = st.sidebar.multiselect("Pick Urgency", df["Urgent/ Planned"].unique())

    filtered_df = df
    if vendor_status:
        filtered_df = filtered_df[filtered_df["Vendor name"].isin(vendor_status)]

    if urgent_planned:
        filtered_df = filtered_df[filtered_df["Urgent/ Planned"].isin(urgent_planned)]

    # Check for necessary columns
    required_columns = ["Project", "PO Total Including GST", "Invoice status", "Lead time", "Sub caterogy"]
    missing_columns = [col for col in required_columns if col not in filtered_df.columns]
    
    if missing_columns:
        st.error(f"Missing columns in the uploaded file: {missing_columns}")
    else:
        # Create visualizations
        col1, col2 = st.columns((2))

        with col1:
            st.subheader("PO Total Including GST by Vendor")
            fig1 = px.pie(filtered_df, values="PO Total Including GST", names="Vendor name", hole=0.5)
            fig1.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("PO Total Including GST by Urgency")
            fig2 = px.pie(filtered_df, values="PO Total Including GST", names="Urgent/ Planned", hole=0.5)
            fig2.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig2, use_container_width=True)

        # Other visualizations
        project_df = filtered_df.groupby(by=["Project"], as_index=False)["PO Total Including GST"].sum()

        col1, col2 = st.columns((2))
        with col1:
            st.subheader("Project wise Sales")
            fig3 = px.bar(project_df, x="Project", y="PO Total Including GST", text=['${:,.2f}'.format(x) for x in project_df["PO Total Including GST"]],
                          template="seaborn")
            st.plotly_chart(fig3, use_container_width=True)

        with col2:
            st.subheader("Sub-Category wise Sales")
            sub_category_df = filtered_df.groupby(by=["Sub caterogy"], as_index=False)["PO Total Including GST"].sum()
            fig4 = px.pie(sub_category_df, values="PO Total Including GST", names="Sub caterogy", hole=0.5)
            fig4.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig4, use_container_width=True)

        # Time series analysis
        filtered_df["month_year"] = filtered_df[date_column].dt.to_period("M")
        st.subheader('Time Series Analysis')

        linechart = pd.DataFrame(filtered_df.groupby(filtered_df["month_year"].dt.strftime("%Y-%b"))["PO Total Including GST"].sum()).reset_index()
        fig5 = px.line(linechart, x="month_year", y="PO Total Including GST", labels={"PO Total Including GST": "Amount"}, height=500, width=1000, template="gridon")
        st.plotly_chart(fig5, use_container_width=True)

        # Treemap
        st.subheader("Hierarchical view of Sales using TreeMap")
        fig6 = px.treemap(filtered_df, path=["Project", "Sub caterogy"], values="PO Total Including GST", hover_data=["PO Total Including GST"],
                          color="Sub caterogy")
        fig6.update_layout(width=800, height=650)
        st.plotly_chart(fig6, use_container_width=True)

        # Scatter plot
        st.subheader("Relationship between Sales and Lead Time using Scatter Plot")
        filtered_df["PO Total Including GST"].fillna(0, inplace=True)
        filtered_df["Lead time"].fillna(0, inplace=True)
        scatter_plot = px.scatter(filtered_df, x="PO Total Including GST", y="Lead time", size="PO Total Including GST", color="Project",
                                  hover_name="Sub caterogy", log_x=True, size_max=60)
        st.plotly_chart(scatter_plot, use_container_width=True)
else:
    st.write("Please upload a file to proceed.")

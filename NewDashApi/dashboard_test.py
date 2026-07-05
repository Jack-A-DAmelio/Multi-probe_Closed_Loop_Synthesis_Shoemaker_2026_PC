from dashboard_framework.discovery import discover_panes
from dashboard_framework.dash_adapter import DashAdapter


def main():

    panes = discover_panes("panes")

    print("Loaded panes:")

    for p in panes:
        p.build() 
        print("-", p.NAME, len(p.widgets))

    adapter = DashAdapter(
        panes=panes,
        api_url="http://localhost:5000/api"
    )

    adapter.run()


if __name__ == "__main__":
    main()
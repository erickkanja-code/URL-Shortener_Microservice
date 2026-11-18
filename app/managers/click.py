"""Analytics queries for clicks, aggregated in SQL rather than in Python."""

from sqlalchemy import Date, Select, cast, func, select

from app.models import Click


class ClickManager:
    """Aggregation queries for the Click model.

    The queries return rows of columns rather than Click objects, so run
    them with `db.execute(...)`, not `db.scalars(...)`.
    """

    @staticmethod
    def clicks_per_country(url_id: int) -> Select:
        """Return a query counting a URL's clicks per country, most clicks first.

        Each row has `country` and `total_clicks`.
        """
        total_clicks = func.count(Click.id).label("total_clicks")
        return (
            select(Click.country, total_clicks)
            .where(Click.url_id == url_id)
            .group_by(Click.country)
            .order_by(total_clicks.desc())
        )

    @staticmethod
    def clicks_per_day(url_id: int) -> Select:
        """Return a query counting a URL's clicks per day, oldest day first.

        Each row has `day` and `total_clicks`.
        """
        day = cast(Click.clicked_at, Date).label("day")
        total_clicks = func.count(Click.id).label("total_clicks")
        return (
            select(day, total_clicks)
            .where(Click.url_id == url_id)
            .group_by(day)
            .order_by(day)
        )
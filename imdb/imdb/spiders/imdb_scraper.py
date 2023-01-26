import polars as pl
import scrapy
import seaborn as sns
from pydispatch import dispatcher
from scrapy import signals

"""
Run in the console by calling " scrapy crawl imdb "
"""


class IMDbScraper(scrapy.Spider):
    name = "imdb"
    data = pl.DataFrame()

    def __init__(self, **kwargs):
        dispatcher.connect(self.spider_closed, signals.spider_closed)
        super().__init__(**kwargs)

    def start_requests(self):
        # url = 'https://www.imdb.com/title/tt1486217/'  # Archer
        # url = 'https://www.imdb.com/title/tt1695360/'  # Legend of Korra
        # url = 'https://www.imdb.com/title/tt0944947/'  # Game of Thrones
        # url = "https://www.imdb.com/title/tt0285403/"  # Westworld
        # url = 'https://www.imdb.com/title/tt0285403/'  # Scrubs
        # url = 'https://www.imdb.com/title/tt0460649/'  # HIMYM
        # url = 'https://www.imdb.com/title/tt0108778/'  # Friends
        # url = "https://www.imdb.com/title/tt21031054/"  # Dragon age: Absolution
        # url = "https://www.imdb.com/title/tt3230854/"  # The Expanse
        url = "https://www.imdb.com/title/tt1266020/"  # Parks and recreation

        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response, **kwargs):
        if self.page_has_episode_list_with_selected_season(response):
            episode_ratings = self.extract_episode_ratings(response)
            self.save_episode_ratings_for_season(response, episode_ratings)
        elif self.page_has_episode_list_but_no_selected_season(response):
            yield from self.request_all_season_pages(response)
        else:
            yield self.request_episode_list(response)

    def request_episode_list(self, response):
        return scrapy.Request(
            url=response.url + "episodes", callback=self.parse
        )

    def request_all_season_pages(self, response):
        seasons = [
            s.strip()
            for s in response.css("select#bySeason > option::text").extract()
        ]
        for season in seasons:
            yield scrapy.Request(
                url=response.url + "?season=" + season, callback=self.parse
            )

    def save_episode_ratings_for_season(self, response, score_elements):
        for i in range(len(score_elements)):
            self.data = self.data.vstack(
                pl.DataFrame(
                    {
                        "Season": [response.url.split("=")[-1]],
                        "Episode": [i + 1],
                        "Rating": [score_elements[i]],
                    }
                )
            )
        self.data.rechunk()

    @staticmethod
    def page_has_episode_list_with_selected_season(response):
        """The URL contains a selected season, and is on the episode list page"""
        return "season" in response.url.split("/")[-1]

    @staticmethod
    def page_has_episode_list_but_no_selected_season(response):
        """The URL is for the episode list page."""
        return "episodes" in response.url.split("/")[-1]

    @staticmethod
    def extract_episode_ratings(response):
        score_elements = response.css(
            "#episodes_content > div.clear > div.list.detail.eplist > div > div.info > "
            "div.ipl-rating-widget > div.ipl-rating-star.small > "
            "span.ipl-rating-star__rating::text"
        ).extract()
        return score_elements

    def spider_closed(self):
        self.preprocess_scores()
        self.plot_and_save_scores()
        return None

    def preprocess_scores(self):
        self.data = self.data.select(
            [
                pl.col("Season").cast(pl.Int16),
                pl.col("Episode").cast(pl.Int16),
                pl.col("Rating").cast(pl.Float32),
            ]
        )
        self.data = self.data.sort(["Season", "Episode"])
        self.data = self.data.with_column(
            pl.arange(0, len(self.data)).alias("Episodes_cumulative")
        )

    def plot_and_save_scores(self):
        g = sns.lmplot(
            data=self.data.to_pandas(),
            x="Episodes_cumulative",
            y="Rating",
            hue="Season",
            height=5,
            aspect=3,
        )
        g.set(ylim=(5, 10))
        g.savefig("rating_per_season.png")

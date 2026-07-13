import math

from app.models.category import Category
from app.models.category_weight import CategoryWeight
from app.models.keyword_weight import KeywordWeight
from app.models.news_item import NewsItem
from app.models.source import Source
from app.services.scoring import decay_learned_weights, update_category_weight


def _make_category(db_session, user_id, name="Tech"):
    cat = Category(user_id=user_id, name=name, keywords=[])
    db_session.add(cat)
    db_session.flush()
    return cat


def _make_source(db_session, user_id):
    source = Source(user_id=user_id, name="Feed", source_type="rss", config={"url": "https://example.com/feed"})
    db_session.add(source)
    db_session.flush()
    return source


def _make_relevant_item(db_session, source, user_id, category, is_relevant=True):
    item = NewsItem(
        source_id=source.id,
        user_id=user_id,
        title="An article",
        url=f"https://example.com/{id(object())}",
        url_hash=f"hash-{id(object())}",
        is_relevant=is_relevant,
    )
    item.categories = [category]
    db_session.add(item)
    db_session.flush()
    return item


class TestUpdateCategoryWeight:
    def test_no_starred_items_gives_base_weight(self, db_session, make_user):
        user = make_user()
        cat = _make_category(db_session, user.id)

        update_category_weight(db_session, cat.id, base=1.0, multiplier=0.5)

        weight_row = db_session.query(CategoryWeight).filter_by(category_id=cat.id).one()
        assert weight_row.weight == 1.0
        assert weight_row.total_marked == 0

    def test_weight_grows_logarithmically_with_starred_count(self, db_session, make_user):
        user = make_user()
        cat = _make_category(db_session, user.id)
        source = _make_source(db_session, user.id)
        for _ in range(3):
            _make_relevant_item(db_session, source, user.id, cat, is_relevant=True)

        update_category_weight(db_session, cat.id, base=1.0, multiplier=0.5)

        weight_row = db_session.query(CategoryWeight).filter_by(category_id=cat.id).one()
        expected = 1.0 + math.log1p(3) * 0.5
        assert weight_row.weight == expected
        assert weight_row.total_marked == 3

    def test_weight_is_recomputed_not_accumulated_on_repeat_calls(self, db_session, make_user):
        """update_category_weight recomputes from the current star count each
        time; it must not compound across repeated calls with no new stars."""
        user = make_user()
        cat = _make_category(db_session, user.id)
        source = _make_source(db_session, user.id)
        _make_relevant_item(db_session, source, user.id, cat, is_relevant=True)

        update_category_weight(db_session, cat.id, base=1.0, multiplier=0.5)
        first = db_session.query(CategoryWeight).filter_by(category_id=cat.id).one().weight
        update_category_weight(db_session, cat.id, base=1.0, multiplier=0.5)
        second = db_session.query(CategoryWeight).filter_by(category_id=cat.id).one().weight

        assert first == second

    def test_never_goes_negative(self, db_session, make_user):
        user = make_user()
        cat = _make_category(db_session, user.id)

        update_category_weight(db_session, cat.id, base=0.0, multiplier=0.5, ignore_penalty=10.0)

        weight_row = db_session.query(CategoryWeight).filter_by(category_id=cat.id).one()
        assert weight_row.weight >= 0.0


class TestDecayLearnedWeights:
    def test_skips_users_with_factor_at_or_above_one(self, db_session, make_user):
        user = make_user()
        db_session.add(KeywordWeight(user_id=user.id, keyword="ai", weight=5.0, total_marked=10))
        db_session.commit()

        result = decay_learned_weights(db_session, {user.id: 1.0})

        kw = db_session.query(KeywordWeight).filter_by(user_id=user.id, keyword="ai").one()
        assert kw.weight == 5.0
        assert result["decayed_keywords"] == 0

    def test_decays_weight_above_prune_threshold(self, db_session, make_user):
        user = make_user()
        db_session.add(KeywordWeight(user_id=user.id, keyword="ai", weight=5.0, total_marked=10))
        db_session.commit()

        result = decay_learned_weights(db_session, {user.id: 0.9})

        kw = db_session.query(KeywordWeight).filter_by(user_id=user.id, keyword="ai").one()
        assert kw.weight == 5.0 * 0.9
        assert result["decayed_keywords"] == 1
        assert result["pruned_keywords"] == 0

    def test_prunes_weight_that_decays_below_threshold(self, db_session, make_user):
        user = make_user()
        # weight * factor must fall to <= 1.001 to be pruned; use a tiny weight.
        db_session.add(KeywordWeight(user_id=user.id, keyword="stale", weight=1.05, total_marked=1))
        db_session.commit()

        result = decay_learned_weights(db_session, {user.id: 0.9})

        remaining = db_session.query(KeywordWeight).filter_by(user_id=user.id, keyword="stale").first()
        assert remaining is None
        assert result["pruned_keywords"] == 1

    def test_only_decays_the_specified_user(self, db_session, make_user):
        user1 = make_user(username="u1")
        user2 = make_user(username="u2")
        db_session.add(KeywordWeight(user_id=user1.id, keyword="ai", weight=5.0, total_marked=10))
        db_session.add(KeywordWeight(user_id=user2.id, keyword="ai", weight=5.0, total_marked=10))
        db_session.commit()

        decay_learned_weights(db_session, {user1.id: 0.5})

        kw1 = db_session.query(KeywordWeight).filter_by(user_id=user1.id, keyword="ai").one()
        kw2 = db_session.query(KeywordWeight).filter_by(user_id=user2.id, keyword="ai").one()
        assert kw1.weight == 2.5
        assert kw2.weight == 5.0

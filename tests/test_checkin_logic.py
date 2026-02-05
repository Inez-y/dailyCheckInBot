import pytest

@pytest.mark.asyncio
async def test_checkin_db_called(monkeypatch):
    from cogs.checkin import CheckIn

    class DummyUser:
        id = 1
        display_name = "TestUser"
        mention = "@TestUser"

    class DummyGuild:
        id = 123

    class DummyResponse:
        async def send_message(self, *args, **kwargs):
            pass

    class DummyInteraction:
        guild = DummyGuild()
        user = DummyUser()
        response = DummyResponse()

    async def fake_add_checkin(guild_id, user_id, nickname, current_date):
        return True

    async def fake_count_user_checkins(guild_id, user_id, current_month):
        return (1, 5)

    monkeypatch.setattr("utils.database.db.add_checkin", fake_add_checkin)
    monkeypatch.setattr("utils.database.db.count_user_checkins", fake_count_user_checkins)

    cog = CheckIn(bot=None)

    await CheckIn.checkin.callback(cog, DummyInteraction())

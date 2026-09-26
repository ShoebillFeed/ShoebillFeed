"""Schemas are derived from each tool function's signature by mcp 2.x.

Under the 1.x low-level API these were hand-written JSON blocks that could
drift from the handler; these tests pin the properties that drift would
break.
"""

import asyncio


def _tools(server):
    return {t.name: t for t in asyncio.run(server.mcp.list_tools())}


class TestRegistration:
    def test_every_tool_is_described(self, server):
        # An undescribed tool is unusable to a model.
        assert all(t.description for t in _tools(server).values())

    def test_every_schema_is_an_object(self, server):
        assert all(t.input_schema.get("type") == "object" for t in _tools(server).values())

    def test_required_arguments_are_derived_from_the_signature(self, server):
        tools = _tools(server)
        assert tools["get_item"].input_schema["required"] == ["id"]
        assert set(tools["set_category_weight"].input_schema["required"]) == {
            "category_id", "manual_weight"}

    def test_optional_arguments_are_not_marked_required(self, server):
        schema = _tools(server)["update_source"].input_schema
        assert schema["required"] == ["id"]
        assert set(schema["properties"]) == {
            "id", "name", "config", "is_active", "fetch_interval"}

    def test_a_no_argument_tool_declares_no_properties(self, server):
        assert _tools(server)["mark_all_read"].input_schema.get("properties", {}) == {}

    def test_tools_taking_a_name_argument_register_correctly(self, server):
        # The dispatch helper's own first parameter is positional-only
        # precisely so these four don't collide with it.
        for name in ("add_source", "update_source", "add_category", "update_category"):
            assert "name" in _tools(server)[name].input_schema["properties"]

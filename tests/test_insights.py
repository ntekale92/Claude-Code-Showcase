from types import SimpleNamespace

import pytest

from oda import insights


@pytest.fixture(scope="module")
def pack(warehouse):
    return insights.build_facts(warehouse)


def test_fact_pack_has_both_domains(pack):
    ids = {f.id for f in pack.facts}
    assert any(i.startswith("nsw.") for i in ids)
    assert "uk.fuel.bev.share_pct" in ids


def test_offline_brief_is_grounded(pack):
    brief = insights.brief_offline(pack)
    assert insights.check_brief(brief, pack) == []
    assert any("SAMPLE DATA" in c for c in brief["caveats"])


def test_eval_cases_all_behave(pack):
    import run_evals

    passed, total, lines = run_evals.run_checker_suite(pack)
    assert passed == total, "\n".join(lines)


def test_claude_path_uses_forced_tool_and_cached_system_prompt(pack):
    """No network: a fake client records the request and returns a tool_use block."""
    captured = {}
    brief = insights.brief_offline(pack)

    class FakeMessages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(content=[SimpleNamespace(type="tool_use", name="submit_brief", input=brief)])

    out = insights.brief_with_claude(pack, client=SimpleNamespace(messages=FakeMessages()))
    assert out == brief
    assert captured["tool_choice"] == {"type": "tool", "name": "submit_brief"}
    assert captured["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "Facts:" in captured["messages"][0]["content"]

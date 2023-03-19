from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner
from nonebug.app import App

from .utils import get_file


def test_cli_help(app: App):
    from nonebot_bison.script.cli import cli

    runner = CliRunner()

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0

    for arg in ["subs-export", "subs-import"]:
        assert arg not in result.output

    for arg in ["export", "import"]:
        assert arg in result.output

    result = runner.invoke(cli, ["export", "--help"])
    assert result.exit_code == 0

    for opt in ["--path", "-p", "导出路径", "--format", "指定导出格式[json, yaml]，默认为 json"]:
        assert opt in result.output

    result = runner.invoke(cli, ["import", "--help"])
    assert result.exit_code == 0

    for opt in ["--path", "-p", "导入文件名", "--format", "指定导入格式[json, yaml]，默认为 json"]:
        assert opt in result.output


async def test_subs_export(app: App, tmp_path: Path):
    from nonebot_bison.config.db_config import config
    from nonebot_bison.script.cli import cli, run_sync
    from nonebot_bison.types import Target as TTarget

    await config.add_subscribe(
        user=123,
        user_type="group",
        target=TTarget("weibo_id"),
        target_name="weibo_name",
        platform_name="weibo",
        cats=[],
        tags=[],
    )
    await config.add_subscribe(
        user=234,
        user_type="group",
        target=TTarget("weibo_id"),
        target_name="weibo_name",
        platform_name="weibo",
        cats=[],
        tags=["kaltsit", "amiya"],
    )
    await config.add_subscribe(
        user=234,
        user_type="group",
        target=TTarget("bilibili_id"),
        target_name="bilibili_name",
        platform_name="bilibili",
        cats=[1, 2],
        tags=[],
    )

    assert len(await config.list_subs_with_all_info()) == 3

    with patch("time.time") as mock_time:
        mock_now = mock_time.now.return_value
        mock_now.time.return_value = 1

        runner = CliRunner()
        # 是否默认导出到工作目录
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = await run_sync(runner.invoke)(cli, ["export"])
            assert result.exit_code == 0
            file_path = Path.cwd() / "bison_subscribes_export_1.json"
            assert file_path.exists()
            assert file_path.stat().st_size

        # 是否导出到指定已存在文件夹
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        result = await run_sync(runner.invoke)(cli, ["export", "-p", str(data_dir)])
        assert result.exit_code == 0
        file_path2 = data_dir / "bison_subscribes_export_1.json"
        assert file_path2.exists()
        assert file_path2.stat().st_size

        # 是否拒绝导出到不存在的文件夹
        result = await run_sync(runner.invoke)(
            cli, ["export", "-p", str(tmp_path / "data2")]
        )
        assert result.exit_code == 1

        # 是否可以以yaml格式导出
        result = await run_sync(runner.invoke)(
            cli, ["export", "-p", str(tmp_path), "--format", "yaml"]
        )
        assert result.exit_code == 0
        file_path3 = tmp_path / "bison_subscribes_export_1.yaml"
        assert file_path3.exists()
        assert file_path3.stat().st_size

        # 是否允许以未支持的格式导出
        result = await run_sync(runner.invoke)(
            cli, ["export", "-p", str(tmp_path), "--format", "toml"]
        )
        assert result.exit_code == 2


async def test_subs_import(app: App, tmp_path):
    from nonebot_bison.config.db_config import config
    from nonebot_bison.script.cli import cli, run_sync

    assert len(await config.list_subs_with_all_info()) == 0

    mock_file: Path = tmp_path / "1.json"
    mock_file.write_text(get_file("subs_export.json"))

    runner = CliRunner()

    result = await run_sync(runner.invoke)(cli, ["import"])
    assert result.exit_code == 2

    result = await run_sync(runner.invoke)(cli, ["import", "-p"])
    assert result.exit_code == 2

    result = await run_sync(runner.invoke)(cli, ["import", "-p", str(mock_file)])
    assert result.exit_code == 0
    assert len(await config.list_subs_with_all_info()) == 3

    mock_file: Path = tmp_path / "2.yaml"
    mock_file.write_text(get_file("subs_export.yaml"))

    result = await run_sync(runner.invoke)(
        cli, ["import", "-p", str(mock_file), "--format=yml"]
    )
    assert result.exit_code == 0
    assert len(await config.list_subs_with_all_info()) == 6

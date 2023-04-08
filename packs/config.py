from .utility import Configuration

GlobalConfig = Configuration("GlobalConfig")
GameConfig = Configuration("GameConfig",
                           {
                               "DataPath": "project:///game.db",
                               "LogPath": "project:///logs/",
                               "CrashLogPath": "project:///crash/",
                               "PluginPath": "project:///plugins/",
                               "DownloadPath": "project:///downloads/",
                               "IsDebug": True})
SQLConfig = Configuration("SQLConfig", {
    "ChangeInner": False,  # Change in dcur.fetchX()
    # only GameDB.get_history_data, making uid0 and uid1 use User (calling .get_user 2 times)
    "ExpensiveTask": False
})
GlobalConfig.GameConfig = GameConfig
GameConfig.SQLConfig = SQLConfig

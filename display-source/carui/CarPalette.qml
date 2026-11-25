import QtQuick 2.0
import Sailfish.Silica 1.0 as Silica

QtObject {
    property bool day: carController.dayTheme
    readonly property color background: day ? "#e3edf8" : "#17203a"
    readonly property color positive: "#28774e"
    readonly property color negative: "#963b48"
    readonly property color actionText: "white"
    readonly property color text: day ? "#18283c" : "white"
    readonly property color secondary: day ? "#50627a" : "#aebcd4"
    readonly property color card: day ? "#f8fbff" : "#263249"
    readonly property color button: day ? "#dce6f2" : "#354460"
    // The pressed state carries the ambience accent, as Silica controls do.
    readonly property color pressed: Qt.tint(button, Qt.rgba(highlightColor.r, highlightColor.g, highlightColor.b, 0.35))
    // The dock carries a light wash of the ambience accent so that it
    // belongs with the rest of the screen.
    readonly property color dock: Qt.tint(day ? "#edf3f9" : "#dd090c14", Qt.rgba(highlightColor.r, highlightColor.g, highlightColor.b, day ? 0.14 : 0.16))
    readonly property color disabled: day ? "#9aabc0" : "#596071"
    readonly property color gradientTop: day ? "#e3edf8" : "#263657"
    readonly property color gradientMiddle: day ? "#d4e2f2" : "#17203a"
    readonly property color gradientBottom: day ? "#edf0f7" : "#382439"
    readonly property color tile: day ? "#c7d9ed" : "#324560"
    readonly property color oem: day ? "#bdcad9" : "#718294"
    readonly property color inactiveDot: day ? "#8294aa" : "#788193"
    readonly property color batteryCap: day ? "#657a94" : "#aeb5c5"
    readonly property color notice: day ? "#f5faff" : "#ed111a2c"

    // Ambience roles. Each carries the name of the Silica Theme colour it
    // stands for. The two accents follow the phone ambience, adapted to the
    // car's own day or night scheme, which may differ from the phone's. The
    // surfaces stay with the day and night themes above so that text keeps
    // its contrast whatever the ambience.
    readonly property int scheme: day ? Silica.Theme.DarkOnLight : Silica.Theme.LightOnDark
    readonly property color primaryColor: text
    readonly property color secondaryColor: secondary
    readonly property color highlightColor: Silica.Theme.highlightFromColor(Silica.Theme.highlightColor, scheme)
    // Silica's own secondary highlight is too pale for the day surfaces, so
    // the accent is drawn towards the secondary text colour instead.
    readonly property color secondaryHighlightColor: Qt.tint(highlightColor, Qt.rgba(secondary.r, secondary.g, secondary.b, 0.4))
    readonly property color highlightBackgroundColor: button
    readonly property color highlightDimmerColor: background
    readonly property color overlayBackgroundColor: card
}

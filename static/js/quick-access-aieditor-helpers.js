/**
 * 速记创建/编辑页 AiEditor：与知识点页类似的选区浮窗、Markdown 粘贴处理。
 * 依赖全局 antd、React（先于本文件加载）。
 */
(function (global) {
    "use strict";

    var lastfontsize = 14;
    var lastcolor = "yellow";

    function showHeadingSelector(editor, selectedText, htmlText) {
        var modal = global.antd.Modal.confirm({
            title: "选择标题级别",
            content: global.React.createElement(
                "div",
                { style: { padding: "20px" } },
                [
                    global.React.createElement("div", { style: { marginBottom: "15px" } }, "请选择标题级别:"),
                    global.React.createElement(
                        "div",
                        { style: { display: "flex", gap: "10px" } },
                        [
                            global.React.createElement(
                                global.antd.Button,
                                {
                                    type: "primary",
                                    onClick: function () {
                                        modal.destroy();
                                        editor.setContent(ChangeHtmlTextWithTag(selectedText, htmlText, "h1"));
                                    },
                                },
                                "一级标题"
                            ),
                            global.React.createElement(
                                global.antd.Button,
                                {
                                    type: "primary",
                                    onClick: function () {
                                        modal.destroy();
                                        editor.setContent(ChangeHtmlTextWithTag(selectedText, htmlText, "h2"));
                                    },
                                },
                                "二级标题"
                            ),
                            global.React.createElement(
                                global.antd.Button,
                                {
                                    type: "primary",
                                    onClick: function () {
                                        modal.destroy();
                                        editor.setContent(ChangeHtmlTextWithTag(selectedText, htmlText, "h3"));
                                    },
                                },
                                "三级标题"
                            ),
                        ]
                    ),
                ]
            ),
            width: 500,
            footer: null,
        });
    }

    function ChangeHtmlTextWithTag(selectedText, htmlText, tag) {
        var startIndex = htmlText.indexOf(selectedText);
        if (startIndex !== -1) {
            var endIndex = startIndex + selectedText.length;
            var beforeSelection = htmlText.substring(0, startIndex);
            var afterSelection = htmlText.substring(endIndex);
            if (selectedText.trim() === "") {
                return htmlText;
            }
            return beforeSelection + "</span></p><" + tag + ">" + selectedText + "</" + tag + ">" + afterSelection;
        }
        return htmlText;
    }

    function ChangeHtmlTextWithFontSizeAndColor(selectedText, htmlText, fontSize, color, colorText) {
        colorText = colorText || "black";
        var fontSize_use = 14;
        lastcolor = color;
        lastfontsize = fontSize;
        if (fontSize === 10) {
            var startIndex = htmlText.indexOf(selectedText);
            if (startIndex !== -1) {
                var beforeSelection = htmlText.substring(0, startIndex);
                var parser = new DOMParser();
                var doc = parser.parseFromString(beforeSelection, "text/html");
                var regex = /font-size:\s*([\d.]+)(?:\s*!important)?/gi;
                var fontSizeValues = [];
                doc.querySelectorAll("[style]").forEach(function (element) {
                    var style = element.getAttribute("style");
                    var matches = Array.from(style.matchAll(regex));
                    if (matches.length > 0) {
                        var lastMatch = matches[matches.length - 1][1] || matches[matches.length - 1][0].replace(/[^0-9.]/g, "");
                        fontSizeValues.push(lastMatch);
                    }
                });
                if (fontSizeValues.length) {
                    fontSize_use = fontSizeValues.pop();
                }
            }
        } else {
            fontSize_use = fontSize;
        }
        return (
            '<span style="color: ' +
            colorText +
            ";font-size:" +
            fontSize_use +
            'px;"><mark data-color="' +
            color +
            '" style="background-color:' +
            color +
            "; color: inherit\">" +
            selectedText +
            "</mark></span>"
        );
    }

    function showFontStyleSelector(editor, selectedText) {
        var fontSize = 10;
        function handleSizeChange(value) {
            fontSize = value;
        }
        var modal = global.antd.Modal.confirm({
            title: "选择字体大小和颜色",
            content: global.React.createElement("div", { style: { padding: "10px" } }, [
                global.React.createElement("div", { style: { margin: "5px 0" } }, [
                    global.React.createElement("span", null, "字体大小:"),
                    global.React.createElement(
                        global.antd.Radio.Group,
                        {
                            onChange: function (e) {
                                handleSizeChange(e.target.value);
                            },
                            defaultValue: lastfontsize,
                            style: { display: "flex", flexWrap: "wrap", marginLeft: "5px" },
                        },
                        [
                            global.React.createElement(global.antd.Radio, { value: 10 }, "10px"),
                            global.React.createElement(global.antd.Radio, { value: 14 }, "14px"),
                            global.React.createElement(global.antd.Radio, { value: 16 }, "16px"),
                            global.React.createElement(global.antd.Radio, { value: 18 }, "18px"),
                            global.React.createElement(global.antd.Radio, { value: 20 }, "20px"),
                            global.React.createElement(global.antd.Radio, { value: 24 }, "24px"),
                            global.React.createElement(global.antd.Radio, { value: 28 }, "28px"),
                        ]
                    ),
                ]),
                global.React.createElement(
                    "div",
                    { style: { display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "12px" } },
                    [
                        { bg: "yellow", fg: "black", label: "黄底" },
                        { bg: "red", fg: "white", label: "红底" },
                        { bg: "black", fg: "white", label: "黑底" },
                        { bg: "#00ffff", fg: "#001954", label: "青底" },
                        { bg: "blue", fg: "white", label: "蓝底" },
                        { bg: "#9EBD9A", fg: "#333", label: "薄荷绿" },
                        { bg: "#FD98A2", fg: "white", label: "粉红底" },
                        { bg: "#e4dddd", fg: "#001954", label: "浅灰底" },
                    ].map(function (c) {
                        return global.React.createElement(
                            global.antd.Button,
                            {
                                type: "primary",
                                style: { backgroundColor: c.bg, borderColor: c.bg, color: c.fg },
                                onClick: function () {
                                    var result = ChangeHtmlTextWithFontSizeAndColor(
                                        selectedText,
                                        editor.getHtml(),
                                        fontSize,
                                        c.bg,
                                        c.fg
                                    );
                                    editor.insert(result);
                                    modal.destroy();
                                },
                            },
                            c.label
                        );
                    })
                ),
            ]),
            width: 520,
            footer: null,
        });
    }

    function clearFormat(selectedText) {
        var regex = new RegExp("<[^>]+>|\\s+", "g");
        return selectedText.replace(regex, "");
    }

    function ReplaceSymbol(editor) {
        var htmlText = editor.getHtml();
        var replacements = {
            ",": "，",
            ".": "。",
            "?": "？",
            "!": "！",
            ":": "：",
            ";": "；",
            '"': "“",
            "'": "‘",
        };
        htmlText = htmlText.replace(/(?!<[^>]*)([.,?!:;'"()])(?![^<]*>)/g, function (match) {
            return replacements[match] || match;
        });
        editor.setContent(htmlText);
    }

    function looksLikeMarkdownPaste(text) {
        if (!text || text.trim().length < 5) return false;
        var signals = [
            /^#{1,6}\s+\S/m,
            /^\s{0,3}[-*+]\s+\S/m,
            /^\s*\d+\.\s+\S/m,
            /^>\s+\S/m,
            /```/,
            /\[[^\]]+\]\([^)]*\)/,
            /`[^`\n]+`/,
            /\*\*[^*\n]+\*\*/,
            /^[ \t]*\|[^|\r\n]+\|/m,
            /^[ \t]*-{3,}\s*$/m,
        ];
        var hits = 0;
        for (var i = 0; i < signals.length; i++) {
            if (signals[i].test(text)) hits++;
        }
        var lines = text.split(/\r?\n/).length;
        if (hits >= 2) return true;
        if (hits === 1 && lines >= 2) return true;
        if (hits === 1 && /^#{1,6}\s/m.test(text)) return true;
        if (hits === 1 && /```/.test(text)) return true;
        return false;
    }

    function plainTextToSimpleHtml(plain) {
        var esc = plain
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
        var parts = esc.split(/\r?\n{2,}/);
        var body = parts
            .map(function (p) {
                return "<p>" + p.replace(/\r?\n/g, "<br>") + "</p>";
            })
            .join("");
        return body || "<p></p>";
    }

    function attachQuickAccessMarkdownPasteGuard(aiEditor, mountSelector) {
        var root = document.querySelector(mountSelector);
        if (!root) return;

        function bind(pm) {
            if (!pm || pm.dataset.mdPasteGuardBound === "1") return;
            pm.dataset.mdPasteGuardBound = "1";
            pm.addEventListener(
                "paste",
                function (e) {
                    var inner = aiEditor.innerEditor;
                    if (!inner || !inner.isEditable) return;
                    var cd = e.clipboardData;
                    if (!cd || (cd.files && cd.files.length > 0)) return;
                    var plain = cd.getData("text/plain") || "";
                    if (!plain.trim() || !looksLikeMarkdownPaste(plain)) return;
                    e.preventDefault();
                    e.stopImmediatePropagation();
                    global.antd.Modal.confirm({
                        title: "检测到 Markdown 内容",
                        content: "剪贴板中的文本疑似 Markdown 格式。是否先转换为富文本再插入编辑器？",
                        okText: "转换并插入",
                        cancelText: "不转换（纯文本）",
                        onOk: function () {
                            aiEditor.insertMarkdown(plain);
                        },
                        onCancel: function () {
                            aiEditor.insert(plainTextToSimpleHtml(plain));
                        },
                    });
                },
                true
            );
        }

        bind(root.querySelector(".ProseMirror"));
        var mo = new MutationObserver(function () {
            bind(root.querySelector(".ProseMirror"));
        });
        mo.observe(root, { childList: true, subtree: true });
    }

    var IC_H =
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M13 20H11V13H4V20H2V4H4V11H11V4H13V20ZM21.0005 8V20H19.0005L19 10.204L17 10.74V8.67L19.5005 8H21.0005Z"></path></svg>';
    var IC_CLR =
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="rgba(255,0,0,1)"><path d="M16.5357 15.9465L18.657 13.8252L15.475 10.6432L19.0106 7.10768L16.8892 4.98636L13.3537 8.52189L10.1717 5.33991L8.05041 7.46123L16.5357 15.9465ZM15.1215 17.3607L6.6362 8.87544L3.80777 11.7039L12.293 20.1892L15.1215 17.3607ZM13.3537 5.69346L16.1821 2.86504C16.5727 2.47451 17.2058 2.47451 17.5963 2.86504L21.1319 6.40057C21.5224 6.79109 21.5224 7.42426 21.1319 7.81478L18.3035 10.6432L20.7783 13.1181C21.1689 13.5086 21.1689 14.1418 20.7783 14.5323L13.0002 22.3105C12.6096 22.701 11.9765 22.701 11.5859 22.3105L1.68645 12.411C1.29592 12.0205 1.29592 11.3873 1.68645 10.9968L9.46462 3.21859C9.85515 2.82807 10.4883 2.82807 10.8788 3.21859L13.3537 5.69346Z"></path></svg>';
    var IC_REP =
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="rgba(0,0,0,1)"><path d="M14.4167 6.67891C15.4469 7.77257 16.0001 9 16.0001 10.9897C16.0001 14.4891 13.5436 17.6263 9.96951 19.1768L9.07682 17.7992C12.4121 15.9946 13.0639 13.6539 13.3245 12.178C12.7875 12.4557 12.0845 12.5533 11.3954 12.4895C9.59102 12.3222 8.16895 10.8409 8.16895 9C8.16895 7.067 9.73595 5.5 11.6689 5.5C12.742 5.5 13.7681 5.99045 14.4167 6.67891Z"></path></svg>';
    var IC_FONT =
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="rgba(41,114,244,1)"><path d="M15.2427 4.51149L8.50547 11.2487L7.79836 13.37L6.7574 14.411L9.58583 17.2394L10.6268 16.1985L12.7481 15.4913L19.4853 8.75413L15.2427 4.51149ZM21.6066 8.04702C21.9972 8.43755 21.9972 9.07071 21.6066 9.46124L13.8285 17.2394L11.7071 17.9465L10.2929 19.3607C9.90241 19.7513 9.26925 19.7513 8.87872 19.3607L4.63608 15.1181C4.24556 14.7276 4.24556 14.0944 4.63608 13.7039L6.0503 12.2897L6.7574 10.1683L14.5356 2.39017C14.9261 1.99964 15.5593 1.99964 15.9498 2.39017L21.6066 8.04702ZM15.2427 7.33992L16.6569 8.75413L11.7071 13.7039L10.2929 12.2897L15.2427 7.33992ZM4.28253 16.8859L7.11096 19.7143L5.69674 21.1285L1.4541 19.7143L4.28253 16.8859Z"></path></svg>';
    var IC_LAST =
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="rgba(41,114,244,1)"><path d="M16 8.99669L20.3714 10.7452C20.751 10.8971 21 11.2648 21 11.6737V20.9967C21 21.549 20.5523 21.9967 20 21.9967H4C3.44772 21.9967 3 21.549 3 20.9967V11.6737C3 11.2648 3.24895 10.8971 3.62861 10.7452L8 8.99669H16ZM15.6148 10.9967H8.38517L5 12.3508V19.9967H19V18.9967H8V13.9967H19V12.3508L15.6148 10.9967ZM16 2.99669C16.5523 2.99669 17 3.4444 17 3.99669V7.99669H7V3.99669C7 3.4444 7.44772 2.99669 8 2.99669H16ZM15 4.99669H9V5.99669H15V4.99669Z"></path></svg>';
    var IC_SUP =
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="rgba(255,137,38,1)"><path d="M5.59567 5L10.5 10.9283L15.4043 5H18L11.7978 12.4971L18 19.9943V20H15.4091L10.5 14.0659L5.59092 20H3V19.9943L9.20216 12.4971L3 5H5.59567ZM21.5507 6.5803C21.7042 6.43453 21.8 6.22845 21.8 6C21.8 5.55817 21.4418 5.2 21 5.2C20.5582 5.2 20.2 5.55817 20.2 6C20.2 6.07624 20.2107 6.14999 20.2306 6.21983L19.0765 6.54958C19.0267 6.37497 19 6.1906 19 6C19 4.89543 19.8954 4 21 4C22.1046 4 23 4.89543 23 6C23 6.57273 22.7593 7.08923 22.3735 7.45384L20.7441 9H23V10H19V9L21.5507 6.5803V6.5803Z"></path></svg>';
    var IC_SUB =
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="rgba(255,137,38,1)"><path d="M5.59567 4L10.5 9.92831L15.4043 4H18L11.7978 11.4971L18 18.9943V19H15.4091L10.5 13.0659L5.59092 19H3V18.9943L9.20216 11.4971L3 4H5.59567ZM21.8 16C21.8 15.5582 21.4418 15.2 21 15.2C20.5582 15.2 20.2 15.5582 20.2 16C20.2 16.0762 20.2107 16.15 20.2306 16.2198L19.0765 16.5496C19.0267 16.375 19 16.1906 19 16C19 14.8954 19.8954 14 21 14C22.1046 14 23 14.8954 23 16C23 16.5727 22.7593 17.0892 22.3735 17.4538L20.7441 19H23V20H19V19L21.5507 16.5803C21.7042 16.4345 21.8 16.2284 21.8 16Z"></path></svg>';

    global.attachQuickAccessMarkdownPasteGuard = attachQuickAccessMarkdownPasteGuard;

    global.buildQuickAccessAiEditorOptions = function (extra) {
        extra = extra || {};
        var bubble = {
            enable: true,
            items: [
                "bold",
                "italic",
                "underline",
                "strike",
                "highlight",
                "font-color",
                {
                    id: "shangbiao",
                    title: "上标",
                    icon: IC_SUP,
                    onClick: function (editor) {
                        editor.insert("<sup>" + editor.getSelectedText() + "</sup>");
                    },
                },
                {
                    id: "xiaobiao",
                    title: "下标",
                    icon: IC_SUB,
                    onClick: function (editor) {
                        editor.insert("<sub>" + editor.getSelectedText() + "</sub>");
                    },
                },
                {
                    id: "heading-selector",
                    title: "标题级别",
                    icon: IC_H,
                    onClick: function (editor) {
                        var selectedText = editor.getSelectedText();
                        var htmlText = editor.getHtml();
                        if (selectedText) {
                            showHeadingSelector(editor, selectedText, htmlText);
                        } else {
                            global.antd.Modal.warning({ title: "提示", content: "请先选中要设置为标题的文本" });
                        }
                    },
                },
                {
                    id: "clean-format",
                    title: "清除格式",
                    icon: IC_CLR,
                    onClick: function (editor) {
                        var selectedText = editor.getSelectedText();
                        if (selectedText) {
                            editor.insert(clearFormat(selectedText));
                        } else {
                            global.antd.Modal.warning({ title: "提示", content: "请先选中要清除格式的文本" });
                        }
                    },
                },
                {
                    id: "replace-symbol",
                    title: "替换标点",
                    icon: IC_REP,
                    onClick: function (editor) {
                        ReplaceSymbol(editor);
                    },
                },
                {
                    id: "font-style-selector",
                    title: "大小颜色",
                    icon: IC_FONT,
                    onClick: function (editor) {
                        var selectedText = editor.getSelectedText();
                        if (selectedText) {
                            showFontStyleSelector(editor, selectedText);
                        } else {
                            global.antd.Modal.warning({ title: "提示", content: "请先选中要设置的文本" });
                        }
                    },
                },
                {
                    id: "last-font-style-selector",
                    title: "上次画笔",
                    icon: IC_LAST,
                    onClick: function (editor) {
                        var selectedText = editor.getSelectedText();
                        if (!selectedText) {
                            global.antd.Modal.warning({ title: "提示", content: "请先选中要设置的文本" });
                            return;
                        }
                        var fg =
                            lastcolor === "yellow" ||
                            lastcolor === "#e4dddd" ||
                            lastcolor === "#9EBD9A" ||
                            lastcolor === "#00ffff"
                                ? "#001954"
                                : "white";
                        var result = ChangeHtmlTextWithFontSizeAndColor(
                            selectedText,
                            editor.getHtml(),
                            lastfontsize,
                            lastcolor,
                            fg
                        );
                        editor.insert(result);
                    },
                },
            ],
        };
        return Object.assign(
            {
                pasteAsText: false,
                htmlPasteConfig: {
                    pasteAsText: false,
                    pasteClean: false,
                    clearLineBreaks: false,
                    pasteProcessor: function (html) {
                        return html;
                    },
                },
                textSelectionBubbleMenu: bubble,
            },
            extra
        );
    };
})(window);

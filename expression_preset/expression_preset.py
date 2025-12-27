class ExpressionPresetNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # 共通プロンプト（ベース）
                "common_prompt": ("STRING", {
                    "multiline": True,
                    "default": "1girl, anime style, clean lineart, consistent proportions, high quality, character illustration"
                }),

                # 表情選択（プルダウン）
                "expression": ([
                    "neutral",
                    "smile",
                    "big_smile_closed_eyes",
                    "angry",
                    "sad",
                    "surprised",
                    "embarrassed"
                ],),
            }
        }

    # まとめたprompt文字列 + cfg/denoise/steps を返す例（必要に応じて増減OK）
    RETURN_TYPES = ("STRING", "FLOAT", "FLOAT", "INT")
    RETURN_NAMES = ("prompt", "cfg", "denoise", "steps")

    FUNCTION = "run"
    CATEGORY = "Expression"

    def run(self, common_prompt, expression):
        # 表情ごとの差分プロンプト
        expr_prompt = {
            "neutral": (
                "neutral expression, calm face, relaxed mouth, eyes open, relaxed eyes, "
                "emotionless, natural look, same eye color, consistent eye color"
            ),
            "smile": (
                "gentle smile, soft smile, slightly curved mouth, happy but calm expression, "
                "eyes relaxed"
            ),
            "big_smile_closed_eyes": (
                "big smile, joyful expression, eyes closed, smiling eyes, wide curved mouth, "
                "cheerful, very happy expression, slightly raised cheeks"
            ),
            "angry": (
                "angry expression, furrowed eyebrows, sharp eyes, tight mouth"
            ),
            "sad": (
                "sad expression, downcast eyes, slightly trembling lips, teary eyes"
            ),
            "surprised": (
                "surprised expression, wide eyes, slightly open mouth, raised eyebrows"
            ),
            "embarrassed": (
                "embarrassed expression, blushing cheeks, awkward smile, eyes slightly averted"
            ),
        }[expression]

        # 表情ごとの推奨パラメータ（あなたの知見を反映）
        params = {
            "neutral":     {"steps": 25, "cfg": 8.0, "denoise": 0.28},
            "smile":       {"steps": 25, "cfg": 8.0, "denoise": 0.48},
            "big_smile_closed_eyes": {"steps": 25, "cfg": 8.0, "denoise": 0.48},
            "sad":         {"steps": 25, "cfg": 8.0, "denoise": 0.48},
            "embarrassed": {"steps": 25, "cfg": 8.0, "denoise": 0.48},
            "angry":       {"steps": 25, "cfg": 7.0, "denoise": 0.30},
            "surprised":   {"steps": 25, "cfg": 7.0, "denoise": 0.30},
        }[expression]

        # 共通部＋表情差分を安全に結合（空行・前後空白も吸収）
        base = (common_prompt or "").strip().strip(",")
        diff = (expr_prompt or "").strip().strip(",")

        if base and diff:
            combined = f"{base}, {diff}"
        else:
            combined = base or diff  # どちらか片方だけ

        return (combined, float(params["cfg"]), float(params["denoise"]), int(params["steps"]))

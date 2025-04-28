# ---------- build stage ---------- #
FROM --platform=$BUILDPLATFORM node:20-bookworm-slim AS build
WORKDIR /app

# --- 依存インストール --------------------------------------------------- #
# package.json / lock-file だけ先にコピーしてキャッシュ活用
COPY package.json package-lock.json* ./

# 必要パッケージをインストール
RUN npm ci --include=optional \
 && if [ "$(uname -m)" = "aarch64" ]; then \
        npm i --no-save @rollup/rollup-linux-arm64-gnu; \
    fi \
 && npm cache clean --force

# --- アプリソース ------------------------------------------------------- #
COPY . .

# ビルド (Vite) – react-split-pane-next 追加後は成功する
RUN npm run build   # vite build now succeeds 🎉

# ---------- runtime stage ---------- #
FROM nginx:1.26-alpine
LABEL org.opencontainers.image.source="https://github.com/your-org/ne-navi"

# ビルド成果物を配置
COPY --from=build /app/dist /usr/share/nginx/html

HEALTHCHECK CMD wget -qO- http://localhost/ || exit 1

# Infrastructure RBAC Smoke Test & Manifest Traceability — Round 3

Tài liệu ghi nhận kết quả kiểm thử luồng NGINX Gateway RBAC và hiện vật hạ tầng trong Round 3.

## 1. Thông tin nhánh và Commit

- Baseline branch: `codex/infra-handoff` (`80cdadada5e7bb253427161ea801c82866539ba0`)
- Round 2 branch: `devops/cicd-github-actions` (`ae206335b32b5c0731da4a193810790a04c6ae0a`)
- Round 3 corrective branch: `devops/cicd-round3-infra`
- Pull Request Round 2: [PR #3](https://github.com/supportflow-ai/supportflow-ai-infra/pull/3) (Base: `codex/infra-handoff`, Head: `vonguyenkiet:devops/cicd-github-actions`)

## 2. Kết quả kiểm thử NGINX Gateway RBAC Smoke Test (9/9 Steps)

- Workflow Run: [Run 41121663475](https://github.com/supportflow-ai/supportflow-ai-infra/actions/runs/41121663475) (Success)
- Commit SHA kiểm thử: `2259d3055cafc211ecd8eecf258f5c60de4b5bdf`
- Bằng chứng 9 bước thực thi:
  1. `[1/9] Health passed`: `GET /health` trả về status Healthy.
  2. `[2/9] Login passed`: `POST /api/auth/login` cấp token hợp lệ.
  3. `[3/9] Create ticket passed`: `POST /api/tickets` khởi tạo vé thành công.
  4. `[4/9] Paged list passed`: `GET /api/tickets/me` trả về danh sách phân trang.
  5. `[5/9] Ticket detail passed`: `GET /api/tickets/{id}` trả về chi tiết vé.
  6. `[6/9] Add comment passed`: `POST /api/tickets/{id}/comments` tạo bình luận timeline.
  7. `[7/9] Ticket timeline passed`: `GET /api/tickets/{id}/timeline` trả về danh sách timeline đồng bộ giữa các bản sao qua PostgreSQL store.
  8. `[8/9] Presigned upload URL passed`: `POST /api/tickets/{id}/attachments/upload-url` sinh pre-signed MinIO URL và `storageKey` hợp lệ.
  9. `[9/9] Agent queue RBAC passed`:
     - **Negative check:** Requester gửi yêu cầu đến `/api/tickets/queue?page=1&pageSize=10` nhận chính xác mã trạng thái `403 Forbidden`.
     - **Positive check:** Agent gửi cùng yêu cầu nhận `200 OK` với mảng `items` và `totalCount` kiểu số.

## 3. Chiến lược phát hành MinIO Image qua Trusted Upstream

- MinIO được build từ `deploy/minio/Dockerfile` dựa trên mã nguồn Go chính thức `RELEASE.2025-10-15T17-29-55Z`.
- Image mục tiêu: `ghcr.io/supportflow-ai/servicedesk-minio`
- Tag mục tiêu: `sha-2259d3055cafc211ecd8eecf258f5c60de4b5bdf`
- Trạng thái hiện tại trong Release Manifest: `pending` (Digest: `null`).
- Quy trình kích hoạt: Sẽ tự động build và push khi PR #3 được merge vào nhánh chính thức `codex/infra-handoff`.

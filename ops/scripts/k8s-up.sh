#!/usr/bin/env bash
# 一键上架：构建 ml-api 镜像、导入集群运行时、apply Kustomize、等待关键 Deployment 就绪。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
NAMESPACE="monitoring-stack"
WAIT_ROLLOUT="${WAIT_ROLLOUT:-0}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-120s}"

if ! command -v kubectl >/dev/null 2>&1; then
  echo "错误: 未找到 kubectl，请先安装或配置 PATH。" >&2
  exit 1
fi

if kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
  ns_phase="$(kubectl get namespace "$NAMESPACE" -o jsonpath='{.status.phase}' 2>/dev/null || true)"
  if [[ "$ns_phase" == "Terminating" ]]; then
    echo "检测到 namespace/$NAMESPACE 正在删除，先等待删除完成..."
    kubectl wait --for=delete "namespace/$NAMESPACE" --timeout=180s || true
  fi
fi

SKIP_BUILD="${SKIP_BUILD:-0}"
if [[ "$SKIP_BUILD" != "1" ]]; then
  echo "==> 构建 ml-api 镜像 (Dockerfile: apps/ml-api/Dockerfile)"
  docker build -t ml-api:dev -f "$ROOT/apps/ml-api/Dockerfile" "$ROOT"

  if command -v k3s >/dev/null 2>&1; then
    echo "==> 导入镜像到 Kubernetes(containerd)"
    docker save ml-api:dev | sudo k3s ctr images import -
  else
    echo "警告: 未找到 k3s 命令；若集群在远程，请自行将 ml-api:dev 推送到集群可拉取的镜像仓库，并改 ml-api Deployment 的 image。" >&2
  fi
else
  echo "==> 跳过构建 (SKIP_BUILD=1)"
fi

echo "==> kubectl apply（按新目录 deployments/kustomize 渲染）"
manifest="$(mktemp)"
trap 'rm -f "$manifest"' EXIT
kubectl kustomize "$ROOT/deployments/kustomize" --load-restrictor LoadRestrictionsNone >"$manifest"

apply_output="$(mktemp)"
if ! kubectl apply -f "$manifest" >"$apply_output" 2>&1; then
  if rg -q "provided port is already allocated" "$apply_output"; then
    echo "检测到 NodePort 冲突，自动回退为 k8s 动态分配 NodePort..."
    # 仅在冲突时移除 nodePort 固定值，避免用户手工改 YAML。
    rg -v "^[[:space:]]+nodePort:" "$manifest" | kubectl apply -f -
  else
    cat "$apply_output" >&2
    exit 1
  fi
else
  cat "$apply_output"
fi
rm -f "$apply_output"

if [[ "$WAIT_ROLLOUT" == "1" ]]; then
  echo "==> 等待工作负载就绪（WAIT_ROLLOUT=1, timeout=$WAIT_TIMEOUT）"
  kubectl -n "$NAMESPACE" rollout status statefulset/elasticsearch --timeout="$WAIT_TIMEOUT" || true
  for dep in logstash kibana prometheus alertmanager grafana ml-api; do
    kubectl -n "$NAMESPACE" rollout status "deployment/$dep" --timeout="$WAIT_TIMEOUT" || true
  done
  kubectl -n "$NAMESPACE" rollout status daemonset/node-exporter --timeout="$WAIT_TIMEOUT" || true
  kubectl -n "$NAMESPACE" rollout status daemonset/filebeat --timeout="$WAIT_TIMEOUT" || true
else
  echo "==> 跳过 rollout 阻塞等待（WAIT_ROLLOUT=0）"
  echo "    可用 WAIT_ROLLOUT=1 WAIT_TIMEOUT=180s ./ops/scripts/k8s-up.sh 开启等待"
fi

echo ""
echo "完成。常用 NodePort（宿主机 IP）："
node_ip="$(kubectl get node -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null || true)"
if [[ -z "$node_ip" ]]; then
  node_ip="127.0.0.1"
fi
for svc in ml-api prometheus grafana alertmanager kibana; do
  node_port="$(kubectl -n "$NAMESPACE" get svc "$svc" -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || true)"
  if [[ "$svc" == "grafana" ]]; then
    echo "  $svc        :${node_port:-N/A} -> http://$node_ip:${node_port:-N/A} (admin/admin)"
  else
    echo "  $svc        :${node_port:-N/A} -> http://$node_ip:${node_port:-N/A}"
  fi
done

echo ""
echo "当前 Pod 状态（便于快速排障）："
kubectl -n "$NAMESPACE" get pods -o wide || true

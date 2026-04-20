#!/usr/bin/env bash
# 一键下架：删除整个命名空间（含 PVC、ConfigMap、工作负载等）。
set -euo pipefail

export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
NAMESPACE="${NAMESPACE:-monitoring-stack}"
DELETE_TIMEOUT="${DELETE_TIMEOUT:-120s}"

if ! command -v kubectl >/dev/null 2>&1; then
  echo "错误: 未找到 kubectl。" >&2
  exit 1
fi

echo "==> 删除命名空间 $NAMESPACE"
kubectl delete namespace "$NAMESPACE" --ignore-not-found --wait=false

echo "==> 等待命名空间删除完成（超时: $DELETE_TIMEOUT）"
if kubectl wait --for=delete "namespace/$NAMESPACE" --timeout="$DELETE_TIMEOUT" >/dev/null 2>&1; then
  echo "命名空间已删除。"
else
  echo "警告: 删除超时，可能有 Terminating 资源卡住。" >&2
  echo "可执行以下命令排查：" >&2
  echo "  kubectl get pods -n $NAMESPACE" >&2
  echo "  kubectl get namespace $NAMESPACE -o jsonpath='{.spec.finalizers}'" >&2
fi

echo "完成。"

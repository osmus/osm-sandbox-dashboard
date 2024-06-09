#!/usr/bin/env bash
aws eks update-kubeconfig --region ${AWS_REGION} --name ${EKS_CLUSTER}
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

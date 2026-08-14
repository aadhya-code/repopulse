# Deploying RepoPulse to Azure

This mirrors the EC2 path in `deploy/aws/README.md` almost exactly — the
same Docker Compose stack, just hosted on an Azure VM instead of an EC2
instance. Nothing in the application code changes.

## 1. Sign up for Azure for Students (no credit card, near-instant)

1. Go to https://azure.microsoft.com/en-us/free/students
2. Click "Start for free" and sign in with your **university email**
   (a Thapar Institute address should qualify)
3. Verify your student status — this is typically near-instant, not a
   24-hour hold like a standard account
4. You'll get $100 in credit, valid for 12 months, plus 750 free
   hours/month of a B1s VM under Azure's always-free tier

If your school email isn't accepted for some reason, the fallback is a
regular Azure Free Account (azure.microsoft.com/free) — that one does
require a card for verification, similar to AWS.

## 2. Create the VM

1. In the Azure portal: **Create a resource → Virtual Machine**
2. Image: **Ubuntu Server 24.04 LTS**
3. Size: **B2s** (2 vCPUs, 4GB RAM — a B1s is free but likely too small
   for Mongo + two services running at once; B2s is still cheap and
   covered by your credit)
4. Authentication: SSH public key (generate one if you don't have one:
   `ssh-keygen -t ed25519`)
5. Under **Networking**, allow inbound ports: `22` (SSH), `4000`
   (Node API), `8000` (Python API)
6. Under **Advanced → Custom data**, paste the contents of
   `deploy/azure/cloud-init.yaml` (edit the `git clone` line to point
   at your actual repo URL first — push this project to GitHub if you
   haven't)
7. Review + create

## 3. Connect and fill in real secrets

Wait ~2-3 minutes after creation, then:

```bash
ssh azureuser@<vm-public-ip>
cd repopulse-mvp
nano node-service/.env   # paste your real GitHub token
docker compose up -d --build
```

## 4. Verify

```bash
curl http://<vm-public-ip>:4000/health
curl http://<vm-public-ip>:8000/health
```

## 5. Shut it down when you're not demoing it

Stop (deallocate) the VM from the Azure portal when you're not actively
using it — this pauses billing against your credit. A B2s running 24/7
will burn through the free credit faster than you'd expect.

---

## On using two different clouds across projects

Using Azure here and AWS on a later project is a completely reasonable
call, and arguably a better resume story than defaulting to AWS every
time — "chose Azure for fast student verification here, AWS for
[other project]" shows you can evaluate a platform rather than just
following convention. Just be precise in interviews about which cloud
actually hosted which project; don't blur it into "I've used AWS" if
this particular deployment ran on Azure.

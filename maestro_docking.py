import os
import subprocess

# -------- 配置 --------
SCHRODINGER = "your SCHRODINGER path"
INPUT_SMI = "1w.smi"           # 原始 SMILES 文件
RUN_DIR = "run_dir"             # 所有计算运行在这个目录
LIGPREP_OUT = "1w.maegz"       # LigPrep 输出
GRIDFILE = "/home/dell/workstations/CCNK/glide-grid_6TD3/glide-grid_6TD3.zip"
GLIDE_INPUT = "dock_SP.in"     # Glide 输入文件
NJOBS = 32                  # 并行线程数

# -------- 函数 --------
def run_cmd(cmd, workdir="."):
    """运行 shell 命令"""
    print(f"[CMD] {cmd} (cwd={workdir})")
    result = subprocess.run(cmd, cwd=workdir, shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        print(result.stderr)
        return False
    print(result.stdout)
    return True

def run_ligprep():
    """运行 LigPrep"""
    cmd = f"{SCHRODINGER}/ligprep -ismi {INPUT_SMI} -omae {LIGPREP_OUT} -epik -NJOBS {NJOBS} -HOST localhost:{NJOBS}  -WAIT"
    return run_cmd(cmd, workdir=RUN_DIR)

def write_glide_input():
    """生成 Glide docking 输入文件"""
    in_file = os.path.join(RUN_DIR, GLIDE_INPUT)
    with open(in_file, "w") as f:
        f.write(f"""FORCEFIELD   OPLS_2005
GRIDFILE     {GRIDFILE}
LIGANDFILE   {LIGPREP_OUT}
POSES_PER_LIG   8
POSTDOCK_NPOSE  8
PRECISION   SP
""")

def run_glide():
    """运行 Glide docking"""
    cmd = f"{SCHRODINGER}/glide {GLIDE_INPUT} -NJOBS {NJOBS} -HOST localhost:{NJOBS}  -WAIT"
    return run_cmd(cmd, workdir=RUN_DIR)

# -------- 主流程 --------
if __name__ == "__main__":
    # 创建运行目录
    os.makedirs(RUN_DIR, exist_ok=True)

    # 拷贝 SMILES 文件到运行目录
    run_input_smi = os.path.join(RUN_DIR, os.path.basename(INPUT_SMI))
    if not os.path.exists(run_input_smi):
        import shutil
        shutil.copy(INPUT_SMI, run_input_smi)

    print("=== Step 1: LigPrep ===")
    success = run_ligprep()
    if not success:
        print("LigPrep 失败，退出")
        exit(1)

    print("=== Step 2: 写 Glide 输入文件 ===")
    write_glide_input()

    print("=== Step 3: Glide docking ===")
    success = run_glide()
    if not success:
        print("Glide docking 失败")
        exit(1)

    print(f"✅ 全部任务完成！输出在 {RUN_DIR}/")

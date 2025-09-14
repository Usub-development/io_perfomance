#!/usr/bin/env python3
# scripts/analyze.py
import argparse, re, os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------- helpers ----------
def parse_number(x):
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str):
        s = x.strip().replace(',', '')
        try: return float(s)
        except: return np.nan
    return np.nan

def parse_latency(s):  # -> ms
    if s is None or (isinstance(s, float) and np.isnan(s)): return np.nan
    if isinstance(s, (int, float)): return float(s)
    s = str(s).strip()
    m = re.match(r'^([0-9]*\.?[0-9]+)\s*(us|µs|ms|s)?$', s, re.IGNORECASE)
    if not m: return np.nan
    val, unit = float(m.group(1)), (m.group(2) or 'ms').lower()
    if unit in ('us', 'µs'): return val / 1000.0
    if unit == 'ms': return val
    if unit == 's':  return val * 1000.0
    return val

def normalize_columns(df):
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    ren = {}
    if 'implementation' in df.columns and 'bin' not in df.columns: ren['implementation'] = 'bin'
    if 'name' in df.columns and 'bin' not in df.columns: ren['name'] = 'bin'
    if 'thread' in df.columns and 'threads' not in df.columns: ren['thread'] = 'threads'
    if 'connections' in df.columns and 'conn' not in df.columns: ren['connections'] = 'conn'
    if 'conns' in df.columns and 'conn' not in df.columns: ren['conns'] = 'conn'
    if 'requests/sec' in df.columns and 'rps' not in df.columns: ren['requests/sec'] = 'rps'
    df = df.rename(columns=ren)
    for col in ('threads','conn','port','rps'):
        if col in df.columns: df[col] = df[col].apply(parse_number)
    for col in ('p50','p90','p99','p999'):
        if col in df.columns: df[col] = df[col].apply(parse_latency)
    need = {'bin','threads','rps'}
    missing = need - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    df = df.dropna(subset=['bin','threads','rps'])
    return df

def aggregate(df):
    return (df.groupby(['bin','threads'])
            .agg(runs=('rps','count'),
                 mean_rps=('rps','mean'),
                 median_rps=('rps','median'),
                 std_rps=('rps','std'),
                 mean_p99_ms=('p99','mean') if 'p99' in df.columns else ('rps','size'))
            .reset_index())

# ---------- plotting ----------
def plot_rps_mean(df_agg, outdir, max_threads=None):
    data = df_agg.copy()
    if max_threads: data = data[data['threads'] <= max_threads]
    data = data.sort_values(['bin','threads'])
    plt.figure(figsize=(8,6))
    for b in data['bin'].unique():
        sub = data[data['bin']==b]
        yerr = sub['std_rps'].fillna(0.0).values
        plt.errorbar(sub['threads'], sub['mean_rps'], yerr=yerr, marker='o', capsize=5, label=b)
    plt.title(f'Mean RPS vs Threads' + (f' (<= {max_threads})' if max_threads else ''))
    plt.xlabel('Threads'); plt.ylabel('Requests/sec'); plt.grid(True); plt.legend()
    path = os.path.join(outdir, 'rps_mean.png')
    plt.savefig(path, bbox_inches='tight'); plt.close()
    return path

def plot_rps_median(df_agg, outdir, max_threads=None):
    data = df_agg.copy()
    if max_threads: data = data[data['threads'] <= max_threads]
    data = data.sort_values(['bin','threads'])
    plt.figure(figsize=(8,6))
    for b in data['bin'].unique():
        sub = data[data['bin']==b]
        plt.plot(sub['threads'], sub['median_rps'], marker='o', label=b)
    plt.title(f'Median RPS vs Threads' + (f' (<= {max_threads})' if max_threads else ''))
    plt.xlabel('Threads'); plt.ylabel('Requests/sec'); plt.grid(True); plt.legend()
    path = os.path.join(outdir, 'rps_median.png')
    plt.savefig(path, bbox_inches='tight'); plt.close()
    return path

def plot_p99(df, outdir, max_threads=None):
    if 'p99' not in df.columns: return None
    data = df.copy()
    if max_threads: data = data[data['threads'] <= max_threads]
    data = data.dropna(subset=['p99']).sort_values(['bin','threads'])
    if data.empty: return None
    plt.figure(figsize=(8,6))
    for b in data['bin'].unique():
        sub = data[data['bin']==b]
        plt.plot(sub['threads'], sub['p99'], marker='o', label=b)
    plt.title(f'p99 latency (ms) vs Threads' + (f' (<= {max_threads})' if max_threads else ''))
    plt.xlabel('Threads'); plt.ylabel('p99 latency (ms)'); plt.grid(True); plt.legend()
    path = os.path.join(outdir, 'p99_vs_threads.png')
    plt.savefig(path, bbox_inches='tight'); plt.close()
    return path

# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description='Benchmark analyzer')
    ap.add_argument('--in', dest='inputs', nargs='+', required=True, help='CSV file(s)')
    ap.add_argument('--out', dest='outdir', required=True, help='Output directory')
    ap.add_argument('--max-threads', dest='max_threads', type=int, default=None, help='Trim to <= N threads')
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    frames = []
    for p in args.inputs:
        if not os.path.exists(p): raise FileNotFoundError(p)
        df = pd.read_csv(p)
        frames.append(normalize_columns(df))
    df_all = pd.concat(frames, ignore_index=True)
    df_all = df_all.sort_values(['bin','threads']).reset_index(drop=True)

    df_all.to_csv(os.path.join(args.outdir, 'parsed_merged.csv'), index=False)

    agg = aggregate(df_all)
    agg.to_csv(os.path.join(args.outdir, 'summary_agg.csv'), index=False)

    paths = []
    paths.append(plot_rps_mean(agg, args.outdir, args.max_threads))
    paths.append(plot_rps_median(agg, args.outdir, args.max_threads))
    p99p = plot_p99(df_all, args.outdir, args.max_threads)
    if p99p: paths.append(p99p)

    # short stdout summary
    print('=== Summary (best per impl) ===')
    best = (agg.loc[agg.groupby('bin')['mean_rps'].idxmax()]
    .sort_values('mean_rps', ascending=False)
    [['bin','threads','mean_rps','median_rps']])
    print(best.to_string(index=False))
    print('Saved:', *paths, sep='\n')

if __name__ == '__main__':
    main()

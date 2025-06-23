import pandas as pd
import os
import tkinter as tk
from tkinter import ttk, messagebox
import math

# Arquivo CSV e constantes de taxa
arquivo_csv = "metatrader.csv"
VALOR_TAXA_REGISTRO = 0.16
VALOR_TAXA_EMOLUMENTOS = 0.09

# Robôs disponíveis
robos_disponiveis = ["Radar", "Gladiador"]

# Configuração da janela principal
root = tk.Tk()
root.title("Registro de Operações")
root.geometry("950x500")

def atualizar_tabela():
    for row in tabela.get_children():
        tabela.delete(row)

    if os.path.exists(arquivo_csv):
        df = pd.read_csv(arquivo_csv, dtype=str)

        # Converter textos para float
        for col in ["Taxa de Registro (R$)", "Taxa de Emolumentos (R$)", "Valor da Operação (R$)", "IR (R$)"]:
            df[col] = df[col].str.replace(",", ".").astype(float)

        # Converter data e ordenar
        df["Data"] = pd.to_datetime(df["Data"], format="%d/%m", errors="coerce")
        df = df.sort_values(by="Data", ascending=False, na_position="last")

        # Formatar datas para exibição
        df_str = df.copy()
        df_str["Data"] = df_str["Data"].dt.strftime("%d/%m")

        # Agrupar e somar colunas usando lista para seleção
        df_grouped = df.groupby("Data", as_index=False)[["Taxa de Registro (R$)", "Taxa de Emolumentos (R$)", "Valor da Operação (R$)"]].sum()
        df_grouped["IR (R$)"] = df_grouped.apply(
            lambda row: (row["Valor da Operação (R$)"] - row["Taxa de Registro (R$)"] - row["Taxa de Emolumentos (R$)"]) * 0.01
            if (row["Valor da Operação (R$)"] - row["Taxa de Registro (R$)"] - row["Taxa de Emolumentos (R$)"]) > 0 else 0,
            axis=1
        )
        df_grouped = df_grouped.sort_values(by="Data", ascending=False)
        df_grouped["Data"] = pd.to_datetime(df_grouped["Data"], format="%Y-%m-%d").dt.strftime("%d/%m")

        # Inserir linhas originais
        for _, row in df_str.iterrows():
            valores = [
                row["Data"],
                int(row["Número de Operações"]) if "Número de Operações" in row else "",
                row.get("Robô", ""),
                f"{row['Valor da Operação (R$)']:.2f}".replace(".", ","),
                f"{row['Taxa de Registro (R$)']:.2f}".replace(".", ","),
                f"{row['Taxa de Emolumentos (R$)']:.2f}".replace(".", ","),
                f"{math.floor(row['IR (R$)']*100)/100:.2f}".replace(".", ",")
            ]
            tabela.insert("", tk.END, values=valores)

        # Inserir totais agrupados
        for _, row in df_grouped.iterrows():
            tabela.insert("", tk.END, values=[
                f"TOTAL {row['Data']}",
                "",
                "",
                f"{row['Valor da Operação (R$)']:.2f}".replace(".", ","),
                f"{row['Taxa de Registro (R$)']:.2f}".replace(".", ","),
                f"{row['Taxa de Emolumentos (R$)']:.2f}".replace(".", ","),
                f"{math.floor(row['IR (R$)']*100)/100:.2f}".replace(".", ",")
            ])


def adicionar_dados():
    data = entry_data.get()
    num_operacoes = entry_operacoes.get()
    robo = combo_robo.get()
    valor_operacao = entry_valor_operacao.get().replace(",", ".")

    if not num_operacoes.isdigit():
        messagebox.showerror("Erro", "O número de operações deve ser um número inteiro.")
        return

    try:
        valor_op = float(valor_operacao)
    except ValueError:
        messagebox.showerror("Erro", "Valor da operação inválido.")
        return

    num_operacoes = int(num_operacoes) * 2

    if robo not in robos_disponiveis:
        messagebox.showerror("Erro", "Selecione um robô válido.")
        return

    # Definir taxas de registro e emolumentos conforme o robô selecionado
    if robo == "Radar":
        taxa_registro = num_operacoes * 0.32
        taxa_emolumentos = num_operacoes * 0.18
    else:  # Gladiador
        taxa_registro = num_operacoes * VALOR_TAXA_REGISTRO
        taxa_emolumentos = num_operacoes * VALOR_TAXA_EMOLUMENTOS

    base_ir = valor_op - taxa_registro - taxa_emolumentos
    ir = math.floor(base_ir * 0.01 * 100) / 100 if base_ir > 0 else 0

    novo_dado = pd.DataFrame([{
        "Data": data,
        "Número de Operações": num_operacoes,
        "Robô": robo,
        "Valor da Operação (R$)": f"{valor_op:.2f}".replace(".", ","),
        "Taxa de Registro (R$)": f"{taxa_registro:.2f}".replace(".", ","),
        "Taxa de Emolumentos (R$)": f"{taxa_emolumentos:.2f}".replace(".", ","),
        "IR (R$)": f"{ir:.2f}".replace(".", ",")
    }])

    if os.path.exists(arquivo_csv):
        novo_dado.to_csv(arquivo_csv, mode='a', index=False, header=False, encoding='utf-8')
    else:
        novo_dado.to_csv(arquivo_csv, mode='w', index=False, header=True, encoding='utf-8')

    atualizar_tabela()
    entry_data.delete(0, tk.END)
    entry_operacoes.delete(0, tk.END)
    entry_valor_operacao.delete(0, tk.END)
    combo_robo.set("")
    messagebox.showinfo("Sucesso", "Dados adicionados com sucesso!")


def excluir_registro():
    selecionado = tabela.selection()
    if not selecionado:
        messagebox.showerror("Erro", "Selecione um registro para excluir.")
        return

    valores = tabela.item(selecionado, "values")

    if os.path.exists(arquivo_csv):
        df = pd.read_csv(arquivo_csv, dtype=str)
        df = df[~(
            (df["Data"] == valores[0]) &
            (df["Número de Operações"] == str(valores[1])) &
            (df["Robô"] == valores[2]) &
            (df["Valor da Operação (R$)"] == valores[3])
        )]
        df.to_csv(arquivo_csv, index=False, encoding='utf-8')

    tabela.delete(selecionado)
    messagebox.showinfo("Sucesso", "Registro excluído com sucesso!")

# Layout de entradas
frame_inputs = tk.Frame(root)
frame_inputs.pack(pady=10)

labels = ["Data (DD/MM):", "Nº de Operações:", "Valor da Operação (R$):", "Robô:"]
for i, texto in enumerate(labels):
    tk.Label(frame_inputs, text=texto).grid(row=i, column=0, padx=5, sticky="e")

entry_data = tk.Entry(frame_inputs)
entry_data.grid(row=0, column=1, padx=5)

entry_operacoes = tk.Entry(frame_inputs)
entry_operacoes.grid(row=1, column=1, padx=5)

entry_valor_operacao = tk.Entry(frame_inputs)
entry_valor_operacao.grid(row=2, column=1, padx=5)

combo_robo = ttk.Combobox(frame_inputs, values=robos_disponiveis, state="readonly")
combo_robo.grid(row=3, column=1, padx=5)

btn_adicionar = tk.Button(frame_inputs, text="Adicionar Dados", command=adicionar_dados)
btn_adicionar.grid(row=4, column=0, columnspan=2, pady=10)

# Layout da tabela
frame_tabela = tk.Frame(root)
frame_tabela.pack(pady=10, fill="both", expand=True)

scrollbar = tk.Scrollbar(frame_tabela, orient="vertical")
scrollbar.pack(side="right", fill="y")

colunas = (
    "Data", "Número de Operações", "Robô", "Valor da Operação (R$)",
    "Taxa de Registro (R$)", "Taxa de Emolumentos (R$)", "IR (R$)"
)

tabela = ttk.Treeview(frame_tabela, columns=colunas, show="headings", yscrollcommand=scrollbar.set)
scrollbar.config(command=tabela.yview)

for col in colunas:
    tabela.heading(col, text=col)
    tabela.column(col, anchor="center", width=130)

tabela.pack(fill="both", expand=True)

btn_excluir = tk.Button(root, text="Excluir Registro Selecionado", command=excluir_registro)
btn_excluir.pack(pady=10)

atualizar_tabela()
root.mainloop()
import streamlit as st
import json
import os
import hashlib

USERS_FILE = 'usuarios.json'
TASKS_FILE = 'tarefas.json'

def load_json(path, default):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return default
    return default

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def hash_password(pw):
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

def find_user(users, username):
    for u in users:
        if u.get('username') == username:
            return u
    return None

def load_data():
    if 'users' not in st.session_state:
        st.session_state.users = load_json(USERS_FILE, [])
    if 'tasks' not in st.session_state:
        st.session_state.tasks = load_json(TASKS_FILE, [])

def save_users():
    save_json(USERS_FILE, st.session_state.users)

def save_tasks():
    save_json(TASKS_FILE, st.session_state.tasks)

def main():
    st.set_page_config(page_title="Gerenciador de Tarefas", page_icon="📋", layout="centered")
    
    st.title("Gerenciador de Tarefas")
    
    if 'logged_user' not in st.session_state:
        st.session_state.logged_user = None

    load_data()

    # Fluxo para usuário não autenticado
    if st.session_state.logged_user is None:
        st.write("Bem-vindo! Faça login ou crie uma conta para acessar suas tarefas.")
        tab1, tab2 = st.tabs(["Entrar", "Registrar"])
        
        with tab1:
            st.header("Login")
            with st.form("login_form"):
                username = st.text_input("Usuário")
                password = st.text_input("Senha", type="password")
                submit_login = st.form_submit_button("Entrar")
                
                if submit_login:
                    if not username or not password:
                        st.warning("Preencha todos os campos.")
                    else:
                        user = find_user(st.session_state.users, username)
                        if not user:
                            st.error("Usuário não encontrado.")
                        elif user['password_hash'] != hash_password(password):
                            st.error("Senha incorreta.")
                        else:
                            st.session_state.logged_user = username
                            st.session_state.logged_full_name = user.get('full_name', username)
                            st.success(f"Bem-vindo, {st.session_state.logged_full_name}!")
                            st.rerun()
                            
        with tab2:
            st.header("Registro de usuário")
            with st.form("register_form"):
                reg_username = st.text_input("Escolha um usuário")
                reg_fullname = st.text_input("Nome completo")
                reg_password = st.text_input("Senha", type="password")
                reg_password_confirm = st.text_input("Confirme a senha", type="password")
                submit_register = st.form_submit_button("Registrar")
                
                if submit_register:
                    if not reg_username or not reg_fullname or not reg_password or not reg_password_confirm:
                        st.warning("Preencha todos os campos.")
                    elif find_user(st.session_state.users, reg_username):
                        st.error("Usuário já existe.")
                    elif reg_password != reg_password_confirm:
                        st.error("Senhas não coincidem.")
                    elif len(reg_password) < 4:
                        st.error("A senha deve ter pelo menos 4 caracteres.")
                    else:
                        st.session_state.users.append({
                            'username': reg_username,
                            'password_hash': hash_password(reg_password),
                            'full_name': reg_fullname
                        })
                        save_users()
                        st.success("Usuário registrado com sucesso! Você já pode fazer login.")
    
    # Fluxo para usuário autenticado (Dashboard)
    else:
        st.sidebar.title(f"Bem-vindo(a), {st.session_state.logged_full_name}")
        if st.sidebar.button("Desconectar", type="primary"):
            st.session_state.logged_user = None
            st.rerun()

        st.header("Dashboard")
        
        tab_list, tab_create, tab_update, tab_delete = st.tabs([
            "📋 Minhas Tarefas", "➕ Criar Tarefa", "✏️ Atualizar Tarefa", "🗑️ Excluir Tarefa"
        ])
        
        owner = st.session_state.logged_user
        
        with tab_list:
            st.subheader("Minhas Tarefas")
            owner_tasks = [t for t in st.session_state.tasks if t.get('owner') == owner]
            if not owner_tasks:
                st.info("Nenhuma tarefa encontrada. Vá para a aba 'Criar Tarefa' para começar!")
            else:
                for t in sorted(owner_tasks, key=lambda x: x['id']):
                    status = "✅ Concluída" if t.get('done') else "⏳ Pendente"
                    with st.expander(f"[{t['id']}] {t['title']} - {status}"):
                        if t.get('description'):
                            st.write(f"**Descrição:** {t['description']}")
                        else:
                            st.write("*Sem descrição.*")
        
        with tab_create:
            st.subheader("Criar Nova Tarefa")
            with st.form("create_task_form"):
                title = st.text_input("Título da tarefa")
                description = st.text_area("Descrição (opcional)")
                submit_create = st.form_submit_button("Criar")
                
                if submit_create:
                    if not title.strip():
                        st.warning("O título não pode ser vazio.")
                    else:
                        existing_ids = [t['id'] for t in st.session_state.tasks]
                        new_id = max(existing_ids) + 1 if existing_ids else 1
                        st.session_state.tasks.append({
                            'id': new_id,
                            'owner': owner,
                            'title': title.strip(),
                            'description': description.strip(),
                            'done': False
                        })
                        save_tasks()
                        st.success(f"Tarefa '{title.strip()}' criada com sucesso!")
                        st.rerun()

        with tab_update:
            st.subheader("Atualizar Tarefa Existente")
            owner_tasks = [t for t in st.session_state.tasks if t.get('owner') == owner]
            if not owner_tasks:
                st.info("Nenhuma tarefa para atualizar.")
            else:
                task_options = {t['id']: f"[{t['id']}] {t['title']}" for t in owner_tasks}
                selected_task_id = st.selectbox(
                    "Selecione a tarefa a atualizar", 
                    options=list(task_options.keys()), 
                    format_func=lambda x: task_options[x]
                )
                
                selected_task = next((t for t in st.session_state.tasks if t['id'] == selected_task_id and t['owner'] == owner), None)
                
                if selected_task:
                    with st.form("update_task_form"):
                        new_title = st.text_input("Título", value=selected_task['title'])
                        new_desc = st.text_area("Descrição", value=selected_task.get('description', ''))
                        new_done = st.checkbox("Concluída", value=selected_task.get('done', False))
                        
                        submit_update = st.form_submit_button("Atualizar")
                        if submit_update:
                            if not new_title.strip():
                                st.warning("O título não pode ser vazio.")
                            else:
                                selected_task['title'] = new_title.strip()
                                selected_task['description'] = new_desc.strip()
                                selected_task['done'] = new_done
                                save_tasks()
                                st.success("Tarefa atualizada com sucesso!")
                                st.rerun()

        with tab_delete:
            st.subheader("Excluir Tarefa")
            owner_tasks = [t for t in st.session_state.tasks if t.get('owner') == owner]
            if not owner_tasks:
                st.info("Nenhuma tarefa para excluir.")
            else:
                del_task_options = {t['id']: f"[{t['id']}] {t['title']}" for t in owner_tasks}
                del_selected_id = st.selectbox(
                    "Selecione a tarefa a excluir", 
                    options=list(del_task_options.keys()), 
                    format_func=lambda x: del_task_options[x]
                )
                
                with st.form("delete_task_form"):
                    st.warning("Tem certeza de que deseja excluir esta tarefa? Esta ação não pode ser desfeita.")
                    submit_delete = st.form_submit_button("Confirmar Exclusão")
                    if submit_delete:
                        idx = next((i for i, t in enumerate(st.session_state.tasks) if t['id'] == del_selected_id and t['owner'] == owner), None)
                        if idx is not None:
                            st.session_state.tasks.pop(idx)
                            save_tasks()
                            st.success("Tarefa excluída com sucesso!")
                            st.rerun()

if __name__ == '__main__':
    main()

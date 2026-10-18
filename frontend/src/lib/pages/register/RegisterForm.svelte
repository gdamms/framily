<script lang="ts">
  import { m, getLanguage } from "$lib/i18n.svelte";
  import Form from "$lib/ui/form/Form.svelte";
  import UsernameField from "$lib/ui/form/UsernameField.svelte";
  import EmailField from "$lib/ui/form/EmailField.svelte";
  import PasswordField from "$lib/ui/form/PasswordField.svelte";
  import ConfirmPasswordField from "$lib/ui/form/ConfirmPasswordField.svelte";
  import Button from "$lib/ui/Button.svelte";
  import { api } from "$lib/api/index";
  import { authStore } from "$lib/stores/auth";
  import { authView } from "$lib/app";

  let username: string = "";
  let email: string = "";
  let password: string = "";
  let confirmPassword: string = "";
  let errorMessage: string = "";
  let isLoading: boolean = false;

  const handleSubmit = async () => {
    errorMessage = "";

    // Validation
    if (!username || !email || !password || !confirmPassword) {
      errorMessage = m.common_all_fields_required();
      return;
    }

    if (password !== confirmPassword) {
      errorMessage = m.common_passwords_mismatch();
      return;
    }

    if (password.length < 8) {
      errorMessage = m.common_password_too_short();
      return;
    }

    if (username.length < 3 || username.length > 32) {
      errorMessage = m.register_username_length();
      return;
    }

    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      errorMessage = m.register_username_chars();
      return;
    }

    isLoading = true;

    try {
      const response = await api.auth.register(username, email, password, getLanguage());
      await authStore.setToken(response.token);
    } catch (error: any) {
      errorMessage = error.message || m.register_failed();
    } finally {
      isLoading = false;
    }
  };
</script>

<Form title={m.register_title()} {errorMessage} submitHandler={handleSubmit}>
  <UsernameField bind:value={username} />
  <EmailField bind:value={email} />
  <PasswordField bind:value={password} />
  <ConfirmPasswordField bind:value={confirmPassword} />
  <Button type="submit" disabled={isLoading}>{isLoading ? m.register_submitting() : m.register_submit()}</Button>
  <p class="login-link">
    {m.register_have_account()}
    <button type="button" class="link-button" onclick={() => authView.set("login")}>
      {m.register_login_link()}
    </button>
  </p>
</Form>

<style>
  .login-link {
    text-align: center;
    margin-top: 1rem;
    font-size: 0.9rem;
  }

  .link-button {
    background: none;
    border: none;
    padding: 0;
    font: inherit;
    color: var(--color-primary);
    text-decoration: underline;
    cursor: pointer;
  }
</style>

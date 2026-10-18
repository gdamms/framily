<script lang="ts">
  import { m } from "$lib/i18n.svelte";
  import Form from "$lib/ui/form/Form.svelte";
  import PasswordField from "$lib/ui/form/PasswordField.svelte";
  import ConfirmPasswordField from "$lib/ui/form/ConfirmPasswordField.svelte";
  import Button from "$lib/ui/Button.svelte";
  import { api } from "$lib/api/index";
  import { authView, resetToken } from "$lib/app";

  let password: string = "";
  let confirmPassword: string = "";
  let errorMessage: string = "";
  let isDone: boolean = false;
  let isLoading: boolean = false;

  const handleSubmit = async () => {
    errorMessage = "";

    const token = $resetToken;
    if (!token) {
      errorMessage = m.reset_invalid_link();
      return;
    }

    if (!password || !confirmPassword) {
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

    isLoading = true;

    try {
      await api.auth.resetPassword(token, password);
      resetToken.set(null);
      isDone = true;
    } catch (error: any) {
      errorMessage = error.message || m.reset_failed();
    } finally {
      isLoading = false;
    }
  };

  const backToLogin = () => {
    resetToken.set(null);
    authView.set("login");
  };
</script>

<Form title={m.reset_title()} {errorMessage} submitHandler={handleSubmit}>
  {#if isDone}
    <p class="success">{m.reset_done()}</p>
    <Button type="button" onclick={backToLogin}>{m.reset_go_to_login()}</Button>
  {:else}
    <PasswordField bind:value={password} placeholder={m.common_new_password()} />
    <ConfirmPasswordField bind:value={confirmPassword} />
    <Button type="submit" disabled={isLoading}>{isLoading ? m.common_saving() : m.reset_submit()}</Button>
    <p class="login-link">
      <button type="button" class="link-button" onclick={backToLogin}>
        {m.auth_back_to_login()}
      </button>
    </p>
  {/if}
</Form>

<style>
  .success {
    text-align: center;
    margin: 0;
  }

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
